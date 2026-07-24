from fastapi import APIRouter, Depends
from app.models.faq_model import FAQCreate, FAQOut
from app.services.faq_service import FAQService
from app.dependencies.api_key_auth import require_api_key

router = APIRouter(prefix="/faq")

@router.post("")
def create_faq(req: FAQCreate, auth=Depends(require_api_key)):
    fid = FAQService.create_faq(req.section, req.question, req.answer)
    return {"id": fid}

@router.get("")
def list_faq(section: str | None = None):
    docs = FAQService.list_faqs(section)
    return [
        {
            "id": str(d["_id"]),
            "section": d["section"],
            "question": d["question"],
            "answer": d["answer"]
        }
        for d in docs
    ]
