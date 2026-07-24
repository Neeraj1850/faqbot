from app.core.config import settings

# Built lazily so the app still starts when the Pinecone key is missing/invalid.
# The FAQ vector path is best-effort (see chat_router), so any error surfaces at
# call time and is caught there rather than crashing startup.
_index = None


def get_index():
    global _index
    if _index is None:
        from pinecone import Pinecone

        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = pc.Index(settings.PINECONE_INDEX)
    return _index
