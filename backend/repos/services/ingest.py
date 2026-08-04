import shutil
import traceback

from django.utils import timezone

from llm.client import embed_texts
from vectorstore.client import add_chunks, delete_collection

from . import chunker, fetch


def run_ingestion(repository):
    """Runs the full fetch -> chunk -> embed -> store pipeline for a Repository instance.
    Mutates and saves the repository's status as it progresses. Safe to call from a background thread."""
    from repos.models import Repository  # avoid import cycles at module load time

    repo_root = None
    failure_traceback = ''
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

        repository.status = 'chunking'
        repository.save(update_fields=['status', 'updated_at'])

        file_paths = chunker.collect_files(repo_root)

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

        def flush(buffer):
            if not buffer:
                return
            embeddings = embed_texts([c['text'] for c in buffer])
            ids = [f'{repository.id}-{chunk_count - len(buffer) + j}' for j in range(len(buffer))]
            documents = [c['text'] for c in buffer]
            metadatas = [
                {'file_path': c['file_path'], 'start_line': c['start_line'], 'end_line': c['end_line']}
                for c in buffer
            ]
            add_chunks(repository.id, ids, embeddings, documents, metadatas)

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
