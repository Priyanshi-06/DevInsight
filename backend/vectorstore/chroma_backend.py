import chromadb
from django.conf import settings

_client = None


def get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    return _client


def collection_name(repo_id):
    return f'repo_{repo_id}'


def get_or_create_collection(repo_id):
    client = get_client()
    return client.get_or_create_collection(name=collection_name(repo_id))


def delete_collection(repo_id):
    client = get_client()
    try:
        client.delete_collection(name=collection_name(repo_id))
    except Exception:
        pass


def add_chunks(repo_id, ids, embeddings, documents, metadatas):
    collection = get_or_create_collection(repo_id)
    collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)


def query(repo_id, query_embedding, top_k):
    collection = get_or_create_collection(repo_id)
    return collection.query(query_embeddings=[query_embedding], n_results=top_k)


def get_first_chunks(repo_id):
    """Returns the first chunk (start_line == 1) of every indexed file, i.e. the top of each
    file where imports typically live, without needing to re-download the repository."""
    collection = get_or_create_collection(repo_id)
    return collection.get(where={'start_line': 1})
