from fastapi import APIRouter, Depends
from app.models.faq_model import FAQCreate
from app.services.faq_service import FAQService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/faq")


@router.post("")
def create_faq(req: FAQCreate, current_user: dict = Depends(get_current_user)):
    fid = FAQService.create_faq(req.section, req.question, req.answer)
    return {"id": fid}


@router.get("")
def list_faq(
    section: str | None = None, current_user: dict = Depends(get_current_user)
):
    docs = FAQService.list_faqs(section)
    return [
        {
            "id": str(d["_id"]),
            "section": d["section"],
            "question": d["question"],
            "answer": d["answer"],
        }
        for d in docs
    ]
