import requests
from django.conf import settings

BEGINNER_LABEL_HINTS = (
    'good first issue', 'good-first-issue', 'help wanted', 'help-wanted',
    'beginner', 'starter', 'easy', 'first-timers-only', 'low-hanging-fruit',
)


def _github_headers():
    headers = {'Accept': 'application/vnd.github+json'}
    if settings.GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {settings.GITHUB_TOKEN}'
    return headers


def _is_beginner_labeled(labels):
    names = [label.get('name', '').lower() for label in labels]
    return any(hint in name for name in names for hint in BEGINNER_LABEL_HINTS)


def fetch_candidate_issues(owner, repo, limit=10):
    """Fetches open issues (excluding PRs), preferring ones with beginner-friendly labels.
    Returns (issues, beginner_only) where beginner_only indicates whether the results are
    exclusively beginner-labeled or a general-open-issues fallback."""
    resp = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/issues',
        params={'state': 'open', 'per_page': 50, 'sort': 'created', 'direction': 'desc'},
        headers=_github_headers(),
        timeout=15,
    )
    resp.raise_for_status()
    all_issues = [item for item in resp.json() if 'pull_request' not in item]

    for issue in all_issues:
        issue['_beginner_labeled'] = _is_beginner_labeled(issue.get('labels', []))

    beginner = [i for i in all_issues if i['_beginner_labeled']]
    if beginner:
        return beginner[:limit], True

    return all_issues[:limit], False
