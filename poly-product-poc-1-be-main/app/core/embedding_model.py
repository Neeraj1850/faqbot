"""Text embedding backed by Google Gemini's free-tier embedding API.

We use the ``gemini-embedding-001`` model configured to output 1536-dimensional
vectors, matching the existing Pinecone index. The Gemini API is called over
HTTPS, so no large model is downloaded or run locally — only a GEMINI_API_KEY is
needed.

The client is created lazily and reused, so importing this module (and starting
the app) stays fast and does not require the key to be present until the first
embedding call.
"""

import math

from app.core.config import settings

# gemini-embedding-001 returns L2-normalized vectors only at its native 3072
# dimensions. At any smaller output size (like our 1536) Google returns
# unnormalized vectors, so we normalize them ourselves for correct cosine
# similarity in Pinecone.
_NATIVE_DIMENSION = 3072

_client = None


def _get_client():
    """Create the Gemini client once and cache it for reuse."""
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _normalize(vector: list[float]) -> list[float]:
    """L2-normalize a vector so cosine similarity behaves as expected."""
    length = math.sqrt(sum(value * value for value in vector))
    if length == 0:
        return vector
    return [value / length for value in vector]


def embed_text(text: str, is_query: bool = False) -> list[float]:
    """Return the 1536-dimensional Gemini embedding for a piece of text.

    Set is_query=True when embedding a user's search query and False when
    embedding stored FAQ content; Gemini uses the task type to tune the
    embedding for retrieval on each side.
    """
    from google.genai import types

    task_type = "RETRIEVAL_QUERY" if is_query else "RETRIEVAL_DOCUMENT"
    response = _get_client().models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=settings.EMBEDDING_DIMENSIONS,
        ),
    )

    vector = response.embeddings[0].values
    if settings.EMBEDDING_DIMENSIONS != _NATIVE_DIMENSION:
        vector = _normalize(vector)
    return vector
