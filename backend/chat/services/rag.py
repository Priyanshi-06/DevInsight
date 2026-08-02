from django.conf import settings

from llm.client import chat_completion, embed_text
from vectorstore.client import query as vector_query
from vectorstore.selection import select_diverse

SYSTEM_PROMPT = (
    "You are an AI assistant that helps developers understand a specific GitHub codebase. "
    "Answer the user's question using ONLY the provided code context. "
    "Be concise and technical. When you reference code, mention the file path. "
    "If the context does not contain enough information to answer confidently, say so plainly "
    "instead of guessing."
)

# Kept small so a full prompt comfortably fits under low-TPM free-tier rate limits (e.g. Groq's
# free tier is 12,000 tokens/minute, shared across the whole app).
MAX_HISTORY_MESSAGES = 4
MAX_CHARS_PER_CHUNK = 450
MAX_CHARS_PER_HISTORY_MESSAGE = 400


def _truncate(text, max_chars):
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + '…'


def _build_context_block(documents, metadatas):
    parts = []
    for doc, meta in zip(documents, metadatas):
        header = f"# {meta['file_path']} (lines {meta['start_line']}-{meta['end_line']})"
        parts.append(f'{header}\n{_truncate(doc, MAX_CHARS_PER_CHUNK)}')
    return '\n\n---\n\n'.join(parts)


def answer_question(repository, question, history_messages):
    """history_messages: list of {'role': 'user'|'assistant', 'content': str}, oldest first."""
    query_embedding = embed_text(question)
    results = vector_query(repository.id, query_embedding, settings.RAG_CANDIDATE_POOL_SIZE)

    pool_documents = results.get('documents', [[]])[0]
    pool_metadatas = results.get('metadatas', [[]])[0]
    documents, metadatas = select_diverse(pool_documents, pool_metadatas, settings.RAG_TOP_K)

    context_block = _build_context_block(documents, metadatas) if documents else 'No relevant code found.'

    messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    for msg in history_messages[-MAX_HISTORY_MESSAGES:]:
        messages.append({'role': msg['role'], 'content': _truncate(msg['content'], MAX_CHARS_PER_HISTORY_MESSAGE)})

    user_prompt = (
        f'Repository: {repository.owner}/{repository.name}\n\n'
        f'Relevant code context:\n{context_block}\n\n'
        f'Question: {question}'
    )
    messages.append({'role': 'user', 'content': user_prompt})

    answer = chat_completion(messages)

    seen = set()
    citations = []
    for meta in metadatas:
        key = (meta['file_path'], meta['start_line'], meta['end_line'])
        if key in seen:
            continue
        seen.add(key)
        citations.append({
            'file_path': meta['file_path'],
            'start_line': meta['start_line'],
            'end_line': meta['end_line'],
        })

    return answer, citations
