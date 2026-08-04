import shutil
import time
import traceback

from django.utils import timezone

from llm.client import embed_texts
from vectorstore.client import add_chunks, delete_collection

from . import chunker, fetch

try:
    import resource  # Unix only (Render); absent on Windows local dev.
except ImportError:
    resource = None


def _log_mem(label):
    if resource is None:
        return
    # ru_maxrss is peak RSS in KB on Linux (this process, growing monotonically over its life).
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    # flush=True: stdout is fully buffered when not attached to a terminal (gunicorn's case), so
    # without it, output sitting in the buffer is lost outright if the process gets SIGKILL'd by
    # an OOM kill before the buffer is ever flushed — exactly the failure this is meant to catch.
    print(f'[mem] {label}: peak RSS so far = {peak_mb:.1f} MB', flush=True)


def run_ingestion(repository):
    """Runs the full fetch -> chunk -> embed -> store pipeline for a Repository instance.
    Mutates and saves the repository's status as it progresses. Safe to call from a background thread."""
    from repos.models import Repository  # avoid import cycles at module load time

    repo_root = None
    failure_traceback = ''
    _log_mem(f'repo {repository.id} start')
    try:
        repository.status = 'fetching'
        repository.save(update_fields=['status', 'updated_at'])

        metadata = fetch.fetch_repo_metadata(repository.owner, repository.name)
        repository.default_branch = metadata['default_branch']
        repository.description = metadata['description']
        repository.language = metadata['language']
        repository.stars = metadata['stars']
        repository.save()

        # Best-effort: captured right before download so it reflects what's actually indexed.
        # Never fatal — a repo can still be indexed even if the staleness check can't be set up.
        try:
            commit_sha = fetch.fetch_latest_commit_sha(
                repository.owner, repository.name, repository.default_branch,
            )
        except Exception:
            commit_sha = ''

        repo_root = fetch.download_and_extract(repository.owner, repository.name, repository.default_branch)
        _log_mem(f'repo {repository.id} after download')

        repository.status = 'chunking'
        repository.save(update_fields=['status', 'updated_at'])

        file_paths = chunker.collect_files(repo_root)
        _log_mem(f'repo {repository.id} after collect_files ({len(file_paths)} files)')

        repository.file_tree = file_paths
        repository.status = 'embedding'
        repository.save(update_fields=['file_tree', 'status', 'updated_at'])

        delete_collection(repository.id)

        # Chunked and embedded in bounded batches, flushed to the vector store as we go,
        # instead of materializing every chunk of the whole repo in memory at once — a repo
        # with hundreds of files could otherwise hold a large amount of text in RAM simultaneously.
        batch_size = 100
        buffer = []
        chunk_count = 0
        batch_num = 0

        def flush(buffer):
            nonlocal batch_num
            if not buffer:
                return
            t0 = time.monotonic()
            embeddings = embed_texts([c['text'] for c in buffer])
            t1 = time.monotonic()
            ids = [f'{repository.id}-{chunk_count - len(buffer) + j}' for j in range(len(buffer))]
            documents = [c['text'] for c in buffer]
            metadatas = [
                {'file_path': c['file_path'], 'start_line': c['start_line'], 'end_line': c['end_line']}
                for c in buffer
            ]
            add_chunks(repository.id, ids, embeddings, documents, metadatas)
            t2 = time.monotonic()
            batch_num += 1
            print(
                f'[timing] repo {repository.id} batch {batch_num}: '
                f'embed={t1 - t0:.1f}s write={t2 - t1:.1f}s',
                flush=True,
            )
            _log_mem(f'repo {repository.id} after batch {batch_num} ({chunk_count} chunks so far)')

        for rel_path in file_paths:
            for chunk in chunker.chunk_file(repo_root, rel_path):
                buffer.append(chunk)
                chunk_count += 1
                if len(buffer) >= batch_size:
                    flush(buffer)
                    buffer = []
        flush(buffer)

        if chunk_count == 0:
            raise ValueError('No indexable text files were found in this repository.')

        repository.chunk_count = chunk_count
        repository.status = 'completed'
        repository.error_message = ''
        repository.last_indexed_commit_sha = commit_sha
        repository.save()

    except Exception as exc:  # noqa: BLE001 - surface any failure onto the repository record
        repository.status = 'failed'
        repository.error_message = str(exc)
        failure_traceback = traceback.format_exc()
        repository.save()

    finally:
        try:
            job = repository.ingestion_job
            job.finished_at = timezone.now()
            job.log = failure_traceback
            job.save()
        except Exception:
            pass
        if repo_root:
            shutil.rmtree(repo_root, ignore_errors=True)
            parent_tmp = repo_root.rsplit('/', 1)[0]
            shutil.rmtree(parent_tmp, ignore_errors=True)
