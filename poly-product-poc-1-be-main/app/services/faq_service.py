from app.core.mongo import faq_collection
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from bson import ObjectId

class FAQService:

    @staticmethod
    def create_faq(section: str, question: str, answer: str):
        doc = {
            "section": section,
            "question": question,
            "answer": answer
        }
        faq_id = faq_collection.insert_one(doc).inserted_id

        embedding = EmbeddingService.embed_question(question)
        VectorService.upsert_faq(str(faq_id), question, section, answer, embedding)

        return str(faq_id)

    @staticmethod
    def bulk_create(faqs: list[dict]):
        faq_ids = faq_collection.insert_many(faqs).inserted_ids
        return [str(_id) for _id in faq_ids]

    @staticmethod
    def list_faqs(section=None):
        query = {}
        if section:
            query["section"] = section
        return list(faq_collection.find(query))
    
    @staticmethod
    def get_by_ids(ids: list[str]):
        obj_ids = [ObjectId(i) for i in ids]
        return list(faq_collection.find({"_id": {"$in": obj_ids}}))
