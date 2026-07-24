from app.services.faq_service import FAQService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.utils.pdf_parser import parse_pdf_qa


class PDFIngestService:
    @staticmethod
    def ingest(pdf_bytes: bytes):
        faq_pairs = parse_pdf_qa(pdf_bytes)

        faq_docs = []
        for qa in faq_pairs:
            faq_docs.append(
                {
                    "section": qa["section"],
                    "question": qa["question"],
                    "answer": qa["answer"],
                }
            )

        ids = FAQService.bulk_create(faq_docs)

        for idx, qa in zip(ids, faq_docs):
            emb = EmbeddingService.embed_question(qa["question"])
            VectorService.upsert_faq(
                idx, qa["question"], qa["section"], qa["answer"], emb
            )

        return ids
