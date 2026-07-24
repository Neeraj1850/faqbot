from app.core.openai_client import embed_text

class EmbeddingService:
    @staticmethod
    def embed_question(question: str) -> list[float]:
        return embed_text(question)
