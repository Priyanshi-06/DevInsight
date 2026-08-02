from django.conf import settings

from llm.client import chat_completion, embed_text
from vectorstore.client import query as vector_query
from vectorstore.selection import select_diverse

from ..models import Recommendation
from .github_issues import fetch_candidate_issues


def _summarize_issue(repository, issue):
    """Best-effort: grounds the issue in retrieved code chunks and asks the LLM for a short,
    beginner-oriented summary. Falls back to a plain body snippet if the LLM call fails."""
    body = (issue.get('body') or '').strip()
    snippet = body[:300]

    suggested_files = []
    try:
        query_text = f"{issue['title']}\n{body[:1000]}"
        embedding = embed_text(query_text)
        results = vector_query(repository.id, embedding, settings.RAG_CANDIDATE_POOL_SIZE)
        pool_documents = results.get('documents', [[]])[0]
        pool_metadatas = results.get('metadatas', [[]])[0]
        _, metadatas = select_diverse(pool_documents, pool_metadatas, 4)
        suggested_files = sorted({m['file_path'] for m in metadatas})
    except Exception:
        pass

    try:
        files_hint = ', '.join(suggested_files) if suggested_files else 'unknown'
        prompt = (
            f"Repository: {repository.owner}/{repository.name}\n"
            f"Issue #{issue['number']}: {issue['title']}\n"
            f"Issue body:\n{body[:1500] or '(no description provided)'}\n\n"
            f"Code areas that look related based on retrieval: {files_hint}\n\n"
            "In 2-3 sentences, explain what this issue is likely asking for and give a beginner "
            "a starting point for tackling it. Be concrete, not generic."
        )
        summary = chat_completion([
            {'role': 'system', 'content': 'You help new open-source contributors understand issues.'},
            {'role': 'user', 'content': prompt},
        ])
    except Exception:
        summary = snippet or 'No description provided.'

    return summary, suggested_files, snippet


def generate_recommendations(repository, force=False, limit=10):
    if not force:
        existing = list(Recommendation.objects.filter(repository=repository))
        if existing:
            return existing, False, None

    try:
        issues, beginner_only = fetch_candidate_issues(repository.owner, repository.name, limit=limit)
    except Exception as exc:  # noqa: BLE001
        return [], False, f'Could not fetch issues from GitHub: {exc}'

    if force:
        Recommendation.objects.filter(repository=repository).delete()

    if not issues:
        return [], False, 'No open issues were found for this repository (issues may be disabled).'

    message = None
    if not beginner_only:
        message = (
            'No issues labeled "good first issue" or "help wanted" were found — '
            'showing the most recently opened issues instead.'
        )

    created = []
    for issue in issues:
        summary, suggested_files, snippet = _summarize_issue(repository, issue)
        rec, _ = Recommendation.objects.update_or_create(
            repository=repository,
            issue_number=issue['number'],
            defaults={
                'title': issue['title'],
                'url': issue['html_url'],
                'labels': [label.get('name') for label in issue.get('labels', [])],
                'beginner_labeled': issue['_beginner_labeled'],
                'body_snippet': snippet,
                'ai_summary': summary,
                'suggested_files': suggested_files,
            },
        )
        created.append(rec)

    return created, True, message
