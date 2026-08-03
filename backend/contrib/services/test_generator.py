import re

from llm.client import chat_completion, embed_text
from repos.services import fetch
from repos.services.fetch import RepoFetchError
from vectorstore.client import query as vector_query

from ..models import TestSuiteDraft

TEST_RESPONSE_FORMAT_INSTRUCTIONS = (
    "Return your response in exactly this format, with these literal markers on their own lines "
    "and nothing else before ===EXPLANATION=== or after the test code:\n"
    "===EXPLANATION===\n"
    "<2-4 sentences: what these tests cover, including which edge cases and any mocked dependencies>\n"
    "===FRAMEWORK===\n"
    "<the testing framework/library used, e.g. pytest, Jest, JUnit>\n"
    "===TEST_FILE_NAME===\n"
    "<the conventional test file name for this language, e.g. test_core.py or core.test.js>\n"
    "===TEST_CODE===\n"
    "<the COMPLETE content of the new test file, with no markdown code fences and no extra commentary>"
)

TEST_RESPONSE_RE = re.compile(
    r'===EXPLANATION===\s*(?P<explanation>.*?)\s*'
    r'===FRAMEWORK===\s*(?P<framework>.*?)\s*'
    r'===TEST_FILE_NAME===\s*(?P<test_file_name>.*?)\s*'
    r'===TEST_CODE===\s*(?P<test_code>.*)',
    re.DOTALL,
)


class TestGeneratorError(Exception):
    pass


# Kept conservative so prompts fit under low-TPM free-tier chat rate limits (e.g. Groq's free
# tier is 12,000 tokens/minute, shared across the whole app).
MAX_TASK_TEXT_CHARS = 500
MAX_SOURCE_CHARS = 6000
MAX_RELATED_CONTEXT_CHUNKS = 2
MAX_CHARS_PER_RELATED_CHUNK = 400
CANDIDATE_FILE_POOL_SIZE = 8


def _strip_code_fences(text):
    if text.startswith('```'):
        text = re.sub(r'^```[\w]*\n', '', text)
        text = re.sub(r'\n```$', '', text)
    return text


def _pick_target_file_via_rag(repository, task_text):
    embedding = embed_text(task_text)
    results = vector_query(repository.id, embedding, CANDIDATE_FILE_POOL_SIZE)
    metadatas = results.get('metadatas', [[]])[0]
    if not metadatas:
        raise TestGeneratorError('No indexed code was relevant enough to base tests on.')
    return metadatas[0]['file_path']


def _related_context(repository, target_file, query_text):
    """Best-effort extra context from other files, for awareness only — same pattern used by the
    PR draft generator. Never fatal: on any retrieval error, tests are still generated without it."""
    try:
        embedding = embed_text(query_text)
        results = vector_query(repository.id, embedding, CANDIDATE_FILE_POOL_SIZE)
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
    except Exception:
        return 'None'

    parts = []
    for doc, meta in zip(documents, metadatas):
        if meta['file_path'] == target_file:
            continue
        truncated_doc = doc if len(doc) <= MAX_CHARS_PER_RELATED_CHUNK else doc[:MAX_CHARS_PER_RELATED_CHUNK] + '…'
        parts.append(f"# {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})\n{truncated_doc}")
        if len(parts) >= MAX_RELATED_CONTEXT_CHUNKS:
            break
    return '\n\n'.join(parts) or 'None'


def _build_prompt(repository, target_file, source_content, related_context, task_text):
    source_excerpt = (
        source_content if len(source_content) <= MAX_SOURCE_CHARS else source_content[:MAX_SOURCE_CHARS] + '\n…'
    )
    task_block = f'\nAdditional focus requested by the user: {task_text}\n' if task_text else ''

    return (
        f"You are writing tests for the repository {repository.owner}/{repository.name}.\n\n"
        f"Target file to test: {target_file}\n\n"
        f"Full content of {target_file}:\n---\n{source_excerpt}\n---\n\n"
        f"Related context from other files (for awareness only, do not test these directly):\n{related_context}\n"
        f"{task_block}\n"
        "Write a complete, runnable unit test file for the public functions/methods in this file. "
        "Cover the normal/happy path AND meaningful edge cases (empty input, None/null, invalid types, "
        "boundary values, error conditions). Where the code depends on external services, the filesystem, "
        "a database, or network calls, use appropriate mocking so the tests are fast and isolated. "
        "Use the testing framework and conventions idiomatic to this file's language. "
        f"{TEST_RESPONSE_FORMAT_INSTRUCTIONS}"
    )


def generate_test_suite(repository, target_file=None, task_description=None):
    task_text = (task_description or '').strip()[:MAX_TASK_TEXT_CHARS]

    if target_file:
        if target_file not in (repository.file_tree or []):
            raise TestGeneratorError(f"{target_file} isn't in this repository's indexed file tree.")
    else:
        if not task_text:
            raise TestGeneratorError('Provide a target file or describe what to test.')
        target_file = _pick_target_file_via_rag(repository, task_text)

    try:
        source_content, _truncated = fetch.fetch_raw_file(
            repository.owner, repository.name, repository.default_branch, target_file,
        )
    except RepoFetchError as exc:
        raise TestGeneratorError(str(exc))

    related_context = _related_context(repository, target_file, task_text or target_file)

    prompt = _build_prompt(repository, target_file, source_content, related_context, task_text)
    raw_response = chat_completion([
        {'role': 'system', 'content': 'You are a meticulous test engineer who writes clear, well-organized tests.'},
        {'role': 'user', 'content': prompt},
    ], temperature=0.2)

    match = TEST_RESPONSE_RE.search(raw_response or '')
    if not match:
        raise TestGeneratorError('The AI response could not be parsed into a structured test suite. Try again.')

    explanation = match.group('explanation').strip()
    framework = match.group('framework').strip()
    test_file_name = match.group('test_file_name').strip().strip('`')
    test_code = _strip_code_fences(match.group('test_code').strip('\n'))

    if not test_code.strip():
        raise TestGeneratorError('The AI did not generate any test code. Try again.')

    return TestSuiteDraft.objects.create(
        repository=repository,
        target_file=target_file,
        task_description=task_text,
        test_file_name=test_file_name,
        framework=framework,
        explanation=explanation,
        test_code=test_code,
    )
