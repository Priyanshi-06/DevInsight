import difflib
import json
import os
import re
import shutil

import requests
from django.conf import settings

from llm.client import chat_completion, embed_text
from repos.services import fetch
from vectorstore.client import query as vector_query

from ..models import PrDraft, Recommendation

REWRITE_RESPONSE_FORMAT_INSTRUCTIONS = (
    "Return your response in exactly this format, with these literal markers on their own lines "
    "and nothing else before ===EXPLANATION=== or after the file content:\n"
    "===EXPLANATION===\n"
    "<2-4 sentence explanation of the change you made and why>\n"
    "===BRANCH===\n"
    "<a short kebab-case git branch name for this change>\n"
    "===TITLE===\n"
    "<a concise pull request title>\n"
    "===FILE===\n"
    "<the COMPLETE new content of the file, with no markdown code fences and no extra commentary>"
)

REWRITE_RESPONSE_RE = re.compile(
    r'===EXPLANATION===\s*(?P<explanation>.*?)\s*'
    r'===BRANCH===\s*(?P<branch>.*?)\s*'
    r'===TITLE===\s*(?P<title>.*?)\s*'
    r'===FILE===\s*(?P<file>.*)',
    re.DOTALL,
)

INSERT_RESPONSE_FORMAT_INSTRUCTIONS = (
    "Return your response in exactly this format, with these literal markers on their own lines "
    "and nothing else before ===EXPLANATION=== or after the snippet:\n"
    "===EXPLANATION===\n"
    "<2-4 sentence explanation of the new entry/snippet you added and why>\n"
    "===BRANCH===\n"
    "<a short kebab-case git branch name for this change>\n"
    "===TITLE===\n"
    "<a concise pull request title>\n"
    "===INSERT_AFTER_LINE===\n"
    "<the exact line number from the excerpt above, after which to insert the new snippet>\n"
    "===SNIPPET===\n"
    "<ONLY the new snippet to insert, matching the exact formatting/indentation/style of the "
    "surrounding entries, with no markdown code fences and no extra commentary>"
)

INSERT_RESPONSE_RE = re.compile(
    r'===EXPLANATION===\s*(?P<explanation>.*?)\s*'
    r'===BRANCH===\s*(?P<branch>.*?)\s*'
    r'===TITLE===\s*(?P<title>.*?)\s*'
    r'===INSERT_AFTER_LINE===\s*(?P<line>\d+)\s*'
    r'===SNIPPET===\s*(?P<snippet>.*)',
    re.DOTALL,
)


class PrDraftError(Exception):
    pass


# Kept conservative so prompts fit under low-TPM free-tier chat rate limits (e.g. Groq's free
# tier is 12,000 tokens/minute, shared across the whole app).
MAX_TASK_TEXT_CHARS = 1000
MAX_RELATED_CONTEXT_CHUNKS = 2
MAX_CHARS_PER_RELATED_CHUNK = 500
MAX_INSERT_EXCERPT_CHUNKS = 3
MAX_CHARS_PER_INSERT_EXCERPT = 1200

# Retrieval is broader than the prompt context: we look through more candidate files than we'll
# actually send to the LLM in full, so related-context selection has real alternatives to choose
# from even though only 1-2 make it into any single prompt.
CANDIDATE_FILE_POOL_SIZE = 10


def _strip_code_fences(text):
    if text.startswith('```'):
        text = re.sub(r'^```[\w]*\n', '', text)
        text = re.sub(r'\n```$', '', text)
    return text


def _resolve_task_text(repository, issue_number, task_description):
    if task_description:
        return task_description[:MAX_TASK_TEXT_CHARS], issue_number

    if issue_number is None:
        raise PrDraftError('Either issue_number or task_description is required.')

    cached = Recommendation.objects.filter(repository=repository, issue_number=issue_number).first()
    if cached:
        return f'{cached.title}\n\n{cached.body_snippet}', issue_number

    resp = requests.get(
        f'https://api.github.com/repos/{repository.owner}/{repository.name}/issues/{issue_number}',
        timeout=15,
    )
    if resp.status_code != 200:
        raise PrDraftError(f'Could not find issue #{issue_number} on GitHub.')
    data = resp.json()
    body = (data.get('body') or '')[:MAX_TASK_TEXT_CHARS]
    return f"{data['title']}\n\n{body}", issue_number


def _retrieve_context(repository, task_text):
    embedding = embed_text(task_text)
    results = vector_query(repository.id, embedding, CANDIDATE_FILE_POOL_SIZE)
    documents = results.get('documents', [[]])[0]
    metadatas = results.get('metadatas', [[]])[0]
    if not documents:
        raise PrDraftError('No indexed code was relevant enough to draft a change from.')
    return documents, metadatas


def _pick_target_file(repository, metadatas):
    """Picks the single most relevant candidate file and reads its full current content,
    downloading the repo only once. Returns (target_file, original_content, mode), where mode is
    'rewrite' if the file fits MAX_PR_FILE_SIZE_BYTES (safe to send in full to the LLM) or
    'insert' if it's larger (only a relevant excerpt will be sent)."""
    seen = set()
    candidates = []
    for meta in metadatas:
        path = meta['file_path']
        if path not in seen:
            seen.add(path)
            candidates.append(path)

    repo_root = fetch.download_and_extract(repository.owner, repository.name, repository.default_branch)
    try:
        for candidate in candidates:
            full_path = os.path.join(repo_root, candidate.replace('/', os.sep))
            if not os.path.isfile(full_path):
                continue
            size = os.path.getsize(full_path)
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            mode = 'rewrite' if size <= settings.MAX_PR_FILE_SIZE_BYTES else 'insert'
            return candidate, content, mode
        raise PrDraftError('Could not locate any relevant file in the current repository snapshot.')
    finally:
        parent_tmp = repo_root.rsplit('/', 1)[0] if '/' in repo_root else repo_root
        shutil.rmtree(repo_root, ignore_errors=True)
        shutil.rmtree(parent_tmp, ignore_errors=True)


def _build_rewrite_prompt(repository, task_text, target_file, original_content, documents, metadatas):
    related_context = []
    for doc, meta in zip(documents, metadatas):
        if meta['file_path'] == target_file:
            continue
        truncated_doc = doc if len(doc) <= MAX_CHARS_PER_RELATED_CHUNK else doc[:MAX_CHARS_PER_RELATED_CHUNK] + '…'
        related_context.append(f"# {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})\n{truncated_doc}")
    related_block = '\n\n'.join(related_context[:MAX_RELATED_CONTEXT_CHUNKS]) or 'None'

    return (
        f"You are contributing to the repository {repository.owner}/{repository.name}.\n\n"
        f"Task / issue to address:\n{task_text}\n\n"
        f"You have decided the most relevant file to change is: {target_file}\n\n"
        f"Current full content of {target_file}:\n---\n{original_content}\n---\n\n"
        f"Related context from other files (for awareness only, do not rewrite these):\n{related_block}\n\n"
        "Make a minimal, correct, well-formed change to this ONE file that addresses the task. "
        "Preserve existing style and formatting elsewhere in the file. "
        f"{REWRITE_RESPONSE_FORMAT_INSTRUCTIONS}"
    )


def _generate_rewrite_change(repository, task_text, target_file, original_content, documents, metadatas):
    prompt = _build_rewrite_prompt(repository, task_text, target_file, original_content, documents, metadatas)
    raw_response = chat_completion([
        {'role': 'system', 'content': 'You are a careful, senior open-source contributor.'},
        {'role': 'user', 'content': prompt},
    ], temperature=0.1)

    match = REWRITE_RESPONSE_RE.search(raw_response or '')
    if not match:
        raise PrDraftError('The AI response could not be parsed into a structured PR draft. Try again.')

    explanation = match.group('explanation').strip()
    branch_name = match.group('branch').strip().strip('`')
    pr_title = match.group('title').strip()
    new_content = _strip_code_fences(match.group('file').strip('\n'))
    return explanation, branch_name, pr_title, new_content


def _build_insert_prompt(repository, task_text, target_file, excerpt_chunks):
    excerpt_parts = []
    for doc, meta in excerpt_chunks[:MAX_INSERT_EXCERPT_CHUNKS]:
        truncated = doc if len(doc) <= MAX_CHARS_PER_INSERT_EXCERPT else doc[:MAX_CHARS_PER_INSERT_EXCERPT] + '…'
        excerpt_parts.append(f"Lines {meta['start_line']}-{meta['end_line']}:\n{truncated}")
    excerpt_block = '\n\n'.join(excerpt_parts) or 'No excerpt available.'

    return (
        f"You are contributing to the repository {repository.owner}/{repository.name}.\n\n"
        f"Task / issue to address:\n{task_text}\n\n"
        f"The file {target_file} is too large to send in full, so here is the most relevant excerpt, "
        f"with its real line numbers in the file:\n---\n{excerpt_block}\n---\n\n"
        "Based on this excerpt's existing style and structure, write ONE new entry/snippet that "
        "addresses the task, matching the surrounding formatting exactly (same indentation, "
        "punctuation, trailing commas, quoting style, etc.). The insertion line MUST be a complete, "
        "safe boundary between two existing sibling entries (e.g. immediately after a line that only "
        "closes an entry, such as '},' at the same indentation as its siblings) — never a line in the "
        "middle of an existing entry's fields, or you will corrupt the file's structure. "
        "Do not attempt to rewrite or reproduce the rest of the file.\n\n"
        f"{INSERT_RESPONSE_FORMAT_INSTRUCTIONS}"
    )


def _apply_insertion(original_content, insert_after_line, snippet):
    lines = original_content.splitlines()
    idx = max(0, min(insert_after_line, len(lines)))
    snippet_lines = snippet.strip('\n').splitlines()
    new_lines = lines[:idx] + snippet_lines + lines[idx:]
    joined = '\n'.join(new_lines)
    return joined + '\n' if original_content.endswith('\n') else joined


def _generate_insert_change(repository, task_text, target_file, original_content, documents, metadatas):
    excerpt_chunks = [
        (doc, meta) for doc, meta in zip(documents, metadatas) if meta['file_path'] == target_file
    ]
    if not excerpt_chunks:
        raise PrDraftError(f'No relevant excerpt of {target_file} was found to base a change on.')

    prompt = _build_insert_prompt(repository, task_text, target_file, excerpt_chunks)
    raw_response = chat_completion([
        {'role': 'system', 'content': 'You are a careful, senior open-source contributor.'},
        {'role': 'user', 'content': prompt},
    ], temperature=0.1)

    match = INSERT_RESPONSE_RE.search(raw_response or '')
    if not match:
        raise PrDraftError('The AI response could not be parsed into a structured PR draft. Try again.')

    explanation = match.group('explanation').strip()
    branch_name = match.group('branch').strip().strip('`')
    pr_title = match.group('title').strip()
    insert_after_line = int(match.group('line'))
    snippet = _strip_code_fences(match.group('snippet').strip('\n'))

    if not snippet.strip():
        raise PrDraftError('The AI did not propose a meaningful snippet to insert. Try a more specific task description.')

    new_content = _apply_insertion(original_content, insert_after_line, snippet)
    return explanation, branch_name, pr_title, new_content


def _validate_structure(target_file, new_content):
    """Catches the most common way an AI-proposed edit corrupts a file: producing structurally
    invalid output. Currently only checks JSON, where this is cheap and unambiguous — an inserted
    snippet landing mid-object is invalid JSON, not just a matter of taste."""
    if target_file.lower().endswith('.json'):
        try:
            json.loads(new_content)
        except ValueError as exc:
            raise PrDraftError(
                f'The proposed change would make {target_file} invalid JSON ({exc}). '
                'This can happen when the insertion point splits an existing entry. Try again or '
                'use a more specific task description.'
            )


def generate_pr_draft(repository, issue_number=None, task_description=None):
    task_text, issue_number = _resolve_task_text(repository, issue_number, task_description)

    documents, metadatas = _retrieve_context(repository, task_text)
    target_file, original_content, mode = _pick_target_file(repository, metadatas)

    if mode == 'rewrite':
        explanation, branch_name, pr_title, new_content = _generate_rewrite_change(
            repository, task_text, target_file, original_content, documents, metadatas,
        )
    else:
        explanation, branch_name, pr_title, new_content = _generate_insert_change(
            repository, task_text, target_file, original_content, documents, metadatas,
        )

    if new_content.strip() == original_content.strip():
        raise PrDraftError('The AI did not propose a meaningful change. Try a more specific task description.')

    _validate_structure(target_file, new_content)

    diff_text = '\n'.join(difflib.unified_diff(
        original_content.splitlines(),
        new_content.splitlines(),
        fromfile=f'a/{target_file}',
        tofile=f'b/{target_file}',
        lineterm='',
    ))

    return PrDraft.objects.create(
        repository=repository,
        issue_number=issue_number,
        task_description=task_text,
        target_file=target_file,
        branch_name=branch_name,
        pr_title=pr_title,
        explanation=explanation,
        diff_text=diff_text,
    )
