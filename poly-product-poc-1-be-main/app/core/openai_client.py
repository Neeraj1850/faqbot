from app.core.config import settings

# Built lazily so the app still starts when OPENAI_API_KEY is not set. The
# client is only needed for embeddings; callers that hit embed_text without a
# key will get an error they can catch (see chat_router's best-effort FAQ step).
_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI

        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def embed_text(text: str) -> list[float]:
    resp = _get_client().embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text,
    )
    return resp.data[0].embedding
