from app.core.embedding_model import embed_text


class EmbeddingService:
    @staticmethod
    def embed_question(question: str, is_query: bool = False) -> list[float]:
        """Embed FAQ text or a user query into a 1536-dim vector.

        Pass is_query=True at search time (embedding the user's question) so the
        model applies its query instruction; leave it False when embedding
        stored FAQ questions during ingest.
        """
        return embed_text(question, is_query=is_query)
