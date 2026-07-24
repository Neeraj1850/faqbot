"""Search the FAQ knowledge base ("Fetch Source" in the system design).

Three steps: embed the query (OpenAI) -> find similar FAQs (Pinecone) -> load the
full documents (Mongo). Each step logs before and after, so when something is
misconfigured the console shows exactly which stage broke instead of a single
vague warning.

Returns [] on any failure — answering with no FAQ context is better than failing
the whole chat request.
"""

from __future__ import annotations

import logging

from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.faq_service import FAQService

logger = logging.getLogger(__name__)


def _shape_for_frontend(faq_docs: list[dict]) -> list[dict]:
    """Convert Mongo documents into the shape the frontend expects."""
    items = []
    for doc in faq_docs:
        items.append(
            {
                "id": str(doc["_id"]),
                "section": doc["section"],
                "question": doc["question"],
                "answer": doc["answer"],
                "created_at": doc.get("created_at"),
                "updated_at": doc.get("updated_at"),
            }
        )
    return items


def search_faqs(query: str) -> list[dict]:
    """Find FAQ entries relevant to ``query``. Returns [] if anything fails."""
    try:
        logger.info("FAQ step 1: embedding query: %s", query)
        embedding = EmbeddingService.embed_question(query)
        logger.info("FAQ step 1 OK: embedding length %d", len(embedding))
    except Exception:
        logger.exception("FAQ step 1 FAILED: could not embed the query (check OPENAI_API_KEY)")
        return []

    try:
        logger.info("FAQ step 2: querying Pinecone for similar FAQs")
        matches = VectorService.query(embedding)
        logger.info("FAQ step 2 OK: Pinecone returned %d matches", len(matches))
    except Exception:
        logger.exception("FAQ step 2 FAILED: Pinecone query error (check PINECONE_API_KEY/INDEX)")
        return []

    try:
        faq_ids = [match.metadata["faq_id"] for match in matches]
        logger.info("FAQ step 3: fetching %d FAQ ids from Mongo", len(faq_ids))
        faq_docs = FAQService.get_by_ids(faq_ids)
        logger.info("FAQ step 3 OK: Mongo returned %d documents", len(faq_docs))
    except Exception:
        logger.exception("FAQ step 3 FAILED: Mongo lookup error (check MONGO_URI/DB_NAME)")
        return []

    return _shape_for_frontend(faq_docs)
