from django.conf import settings
from openai import OpenAI

_chat_client = None
_openai_embedding_client = None
_local_embedder = None


def get_chat_client():
    """Client for chat completions. Works against OpenAI or any OpenAI-compatible endpoint
    (e.g. Groq) depending on LLM_BASE_URL."""
    global _chat_client
    if _chat_client is None:
        if not settings.LLM_API_KEY:
            raise RuntimeError('LLM_API_KEY is not set. Add it to backend/.env')
        kwargs = {'api_key': settings.LLM_API_KEY}
        if settings.LLM_BASE_URL:
            kwargs['base_url'] = settings.LLM_BASE_URL
        _chat_client = OpenAI(**kwargs)
    return _chat_client


def chat_completion(messages, temperature=0.2):
    client = get_chat_client()
    response = client.chat.completions.create(
        model=settings.LLM_CHAT_MODEL,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def _get_openai_embedding_client():
    global _openai_embedding_client
    if _openai_embedding_client is None:
        if not settings.OPENAI_API_KEY:
            raise RuntimeError('OPENAI_API_KEY is not set (required when EMBEDDING_PROVIDER=openai).')
        _openai_embedding_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_embedding_client


def _get_local_embedder():
    global _local_embedder
    if _local_embedder is None:
        from sentence_transformers import SentenceTransformer
        _local_embedder = SentenceTransformer(settings.LOCAL_EMBEDDING_MODEL)
    return _local_embedder


def embed_texts(texts):
    """Returns a list of embedding vectors, one per input text."""
    texts = list(texts)

    if settings.EMBEDDING_PROVIDER == 'local':
        model = _get_local_embedder()
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=32)
        return embeddings.tolist()

    client = _get_openai_embedding_client()
    batch_size = 100
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        response = client.embeddings.create(model=settings.OPENAI_EMBEDDING_MODEL, input=batch)
        all_embeddings.extend([item.embedding for item in response.data])
    return all_embeddings


def embed_text(text):
    return embed_texts([text])[0]
