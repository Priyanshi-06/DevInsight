import os
from django.conf import settings

SKIP_DIRS = {
    '.git', 'node_modules', 'dist', 'build', '.next', '.venv', 'venv',
    '__pycache__', '.pytest_cache', 'vendor', 'target', '.idea', '.vscode',
    'coverage', '.tox', 'egg-info',
}

SKIP_FILE_SUFFIXES = (
    '.lock', '.min.js', '.min.css', '.map',
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.webp', '.bmp',
    '.woff', '.woff2', '.ttf', '.eot',
    '.zip', '.tar', '.gz', '.rar', '.7z',
    '.mp4', '.mp3', '.wav', '.mov',
    '.pdf', '.exe', '.dll', '.so', '.dylib', '.bin', '.pyc', '.class', '.jar',
)

SKIP_FILENAMES = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock',
    'Cargo.lock', 'go.sum',
}


def _is_probably_binary(sample: bytes) -> bool:
    if b'\x00' in sample:
        return True
    return False


def _is_readme(filename: str) -> bool:
    return os.path.splitext(filename)[0].lower() == 'readme'


def collect_files(repo_root, scoped_paths=None):
    """Walks the extracted repo and returns a sorted list of relative file paths worth indexing.
    If scoped_paths is given (a list of top-level folder names, e.g. ['src', 'backend']), only
    those folders are walked at all — pruned before os.walk descends into anything else, so a
    huge unrelated subtree is never even read from disk, not just filtered out afterward. The root
    README is always included regardless of scope — without it, chat has no project-level context
    to answer "what is this repo about," even though that's exactly the kind of question a scoped
    index should still be able to answer."""
    scoped_set = set(scoped_paths) if scoped_paths else None
    collected = []
    for dirpath, dirnames, filenames in os.walk(repo_root):
        if scoped_set is not None and dirpath == repo_root:
            dirnames[:] = [d for d in dirnames if d in scoped_set]
        else:
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith('.')]
        if scoped_set is not None and dirpath == repo_root:
            filenames = [f for f in filenames if _is_readme(f)]
        for filename in filenames:
            if filename in SKIP_FILENAMES:
                continue
            if filename.lower().endswith(SKIP_FILE_SUFFIXES):
                continue
            full_path = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(full_path)
            except OSError:
                continue
            if size == 0 or size > settings.MAX_FILE_SIZE_BYTES:
                continue
            try:
                with open(full_path, 'rb') as f:
                    if _is_probably_binary(f.read(1024)):
                        continue
            except OSError:
                continue
            rel_path = os.path.relpath(full_path, repo_root).replace(os.sep, '/')
            collected.append(rel_path)

    collected.sort()
    return collected[: settings.MAX_FILES_TO_INDEX]


def chunk_file(repo_root, rel_path):
    """Splits a file's text into overlapping line-based chunks with line-number metadata."""
    full_path = os.path.join(repo_root, rel_path.replace('/', os.sep))
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except OSError:
        return []

    if not lines:
        return []

    chunk_size = settings.CHUNK_LINES
    overlap = settings.CHUNK_OVERLAP_LINES
    step = max(chunk_size - overlap, 1)

    chunks = []
    for start in range(0, len(lines), step):
        end = min(start + chunk_size, len(lines))
        text = ''.join(lines[start:end]).strip()
        if text:
            chunks.append({
                'file_path': rel_path,
                'start_line': start + 1,
                'end_line': end,
                'text': text,
            })
        if end == len(lines):
            break

    return chunks
