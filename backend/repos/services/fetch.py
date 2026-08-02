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
