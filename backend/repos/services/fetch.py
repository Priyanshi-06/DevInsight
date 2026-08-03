import os
import re
import tarfile
import tempfile
import requests
from django.conf import settings

GITHUB_URL_RE = re.compile(r'github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?/?$')


class RepoFetchError(Exception):
    pass


def parse_github_url(url):
    match = GITHUB_URL_RE.search(url.strip())
    if not match:
        raise RepoFetchError(f'Could not parse a GitHub owner/repo from: {url}')
    return match.group(1), match.group(2)


def _github_headers():
    headers = {'Accept': 'application/vnd.github+json'}
    if settings.GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {settings.GITHUB_TOKEN}'
    return headers


def fetch_repo_metadata(owner, repo):
    resp = requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=_github_headers(), timeout=15)
    if resp.status_code == 404:
        raise RepoFetchError(f'Repository {owner}/{repo} not found (is it public?)')
    if resp.status_code == 403:
        raise RepoFetchError('GitHub API rate limit exceeded. Try again later or set GITHUB_TOKEN.')
    resp.raise_for_status()
    data = resp.json()
    return {
        'default_branch': data.get('default_branch', 'main'),
        'description': data.get('description') or '',
        'language': data.get('language') or '',
        'stars': data.get('stargazers_count', 0),
    }


def fetch_latest_commit_sha(owner, repo, branch):
    """The current HEAD commit SHA of a branch — compared against what was actually indexed to
    detect a stale snapshot."""
    resp = requests.get(
        f'https://api.github.com/repos/{owner}/{repo}/commits/{branch}',
        headers=_github_headers(),
        timeout=15,
    )
    if resp.status_code == 403:
        raise RepoFetchError('GitHub API rate limit exceeded. Try again later or set GITHUB_TOKEN.')
    if resp.status_code != 200:
        raise RepoFetchError(f'Could not check the latest commit for {owner}/{repo}@{branch}.')
    return resp.json()['sha']


def fetch_raw_file(owner, repo, branch, path, max_bytes=None):
    """Fetches a single file's raw content via GitHub's raw content endpoint — much lighter than
    download_and_extract() when only one file is needed. Returns (content, truncated)."""
    url = f'https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}'
    resp = requests.get(url, timeout=15)
    if resp.status_code != 200:
        raise RepoFetchError(f'Could not fetch {path} from GitHub (status {resp.status_code}).')

    content_bytes = resp.content
    truncated = bool(max_bytes) and len(content_bytes) > max_bytes
    if truncated:
        content_bytes = content_bytes[:max_bytes]

    try:
        return content_bytes.decode('utf-8'), truncated
    except UnicodeDecodeError:
        raise RepoFetchError('This file appears to be binary and cannot be read as text.')


def download_and_extract(owner, repo, branch):
    """Downloads the repo tarball via GitHub's codeload endpoint and extracts it to a temp dir.
    Returns the path to the extracted repo root (the tarball's single top-level directory)."""
    url = f'https://codeload.github.com/{owner}/{repo}/tar.gz/refs/heads/{branch}'
    resp = requests.get(url, stream=True, timeout=60)
    if resp.status_code != 200:
        raise RepoFetchError(f'Failed to download {owner}/{repo}@{branch} (status {resp.status_code})')

    tmp_dir = tempfile.mkdtemp(prefix=f'{owner}_{repo}_')
    tar_path = f'{tmp_dir}/repo.tar.gz'
    with open(tar_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    with tarfile.open(tar_path, 'r:gz') as tar:
        tar.extractall(path=tmp_dir, filter='data')

    entries = [e for e in os.listdir(tmp_dir) if e != 'repo.tar.gz']
    if not entries:
        raise RepoFetchError('Downloaded archive was empty')
    return f'{tmp_dir}/{entries[0]}'
