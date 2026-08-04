from django.db import connection

from . import chroma_backend, pg_backend


def _backend():
    """Postgres (e.g. Neon) persists across redeploys, unlike a Web Service's local disk where
    ChromaDB's files would otherwise get wiped on every deploy. SQLite-backed local dev has no
    such problem, so it keeps using the simpler file-based ChromaDB store."""
    return pg_backend if connection.vendor == 'postgresql' else chroma_backend


def delete_collection(repo_id):
    return _backend().delete_collection(repo_id)


def add_chunks(repo_id, ids, embeddings, documents, metadatas):
    return _backend().add_chunks(repo_id, ids, embeddings, documents, metadatas)


def query(repo_id, query_embedding, top_k):
    return _backend().query(repo_id, query_embedding, top_k)


def get_first_chunks(repo_id):
    return _backend().get_first_chunks(repo_id)
