from django.conf import settings
from django.db import connection

_schema_ready = False


def _vector_literal(embedding):
    return '[' + ','.join(repr(float(x)) for x in embedding) + ']'


def _ensure_schema():
    global _schema_ready
    if _schema_ready:
        return
    with connection.cursor() as cursor:
        cursor.execute('CREATE EXTENSION IF NOT EXISTS vector')
        cursor.execute(
            f'''
            CREATE TABLE IF NOT EXISTS code_chunks (
                id BIGSERIAL PRIMARY KEY,
                repository_id INTEGER NOT NULL,
                chunk_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                start_line INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                document TEXT NOT NULL,
                embedding VECTOR({settings.EMBEDDING_DIM}) NOT NULL
            )
            '''
        )
        cursor.execute(
            'CREATE INDEX IF NOT EXISTS code_chunks_repository_id_idx ON code_chunks (repository_id)'
        )
    _schema_ready = True


def delete_collection(repo_id):
    _ensure_schema()
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM code_chunks WHERE repository_id = %s', [repo_id])


def add_chunks(repo_id, ids, embeddings, documents, metadatas):
    _ensure_schema()
    if not ids:
        return

    # A single multi-row INSERT instead of executemany, which issues one round trip per row —
    # over a network connection to a hosted Postgres instance (e.g. Neon), that's the difference
    # between 1 round trip and 100 for a batch this size.
    params = []
    for cid, doc, meta, emb in zip(ids, documents, metadatas, embeddings):
        params += [repo_id, cid, meta['file_path'], meta['start_line'], meta['end_line'], doc, _vector_literal(emb)]
    values_sql = ', '.join(['(%s, %s, %s, %s, %s, %s, %s::vector)'] * len(ids))

    with connection.cursor() as cursor:
        cursor.execute(
            f'''
            INSERT INTO code_chunks
                (repository_id, chunk_id, file_path, start_line, end_line, document, embedding)
            VALUES {values_sql}
            ''',
            params,
        )


def query(repo_id, query_embedding, top_k):
    _ensure_schema()
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT document, file_path, start_line, end_line
            FROM code_chunks
            WHERE repository_id = %s
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            ''',
            [repo_id, _vector_literal(query_embedding), top_k],
        )
        rows = cursor.fetchall()

    documents = [r[0] for r in rows]
    metadatas = [{'file_path': r[1], 'start_line': r[2], 'end_line': r[3]} for r in rows]
    # Nested one level, matching chromadb's query() shape (outer list = one per query embedding).
    return {'documents': [documents], 'metadatas': [metadatas]}


def get_first_chunks(repo_id):
    """Returns the first chunk (start_line == 1) of every indexed file, i.e. the top of each
    file where imports typically live, without needing to re-download the repository."""
    _ensure_schema()
    with connection.cursor() as cursor:
        cursor.execute(
            '''
            SELECT document, file_path, start_line, end_line
            FROM code_chunks
            WHERE repository_id = %s AND start_line = 1
            ''',
            [repo_id],
        )
        rows = cursor.fetchall()

    documents = [r[0] for r in rows]
    metadatas = [{'file_path': r[1], 'start_line': r[2], 'end_line': r[3]} for r in rows]
    return {'documents': documents, 'metadatas': metadatas}
