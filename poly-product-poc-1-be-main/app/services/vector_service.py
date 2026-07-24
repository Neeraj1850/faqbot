from app.core.pinecone_client import get_index
from app.core.config import settings

class VectorService:
    @staticmethod
    def upsert_faq(faq_id: str, question: str, section: str, answer: str, embedding: list[float]):
        get_index().upsert(
            vectors=[
                {
                    "id": f"faq::{faq_id}",
                    "values": embedding,
                    "metadata": {
                        "faq_id": faq_id,
                        "question": question,
                        "answer": answer,
                        "section": section
                    }
                }
            ],
            namespace=settings.PINECONE_NAMESPACE
        )

    @staticmethod
    def query(text_embedding: list[float], top_k=3):
        resp = get_index().query(
            vector=text_embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=settings.PINECONE_NAMESPACE
        )
        return resp.matches
