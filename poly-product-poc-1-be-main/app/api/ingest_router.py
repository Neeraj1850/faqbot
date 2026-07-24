from fastapi import APIRouter, UploadFile, Depends
from app.services.pdf_ingest_service import PDFIngestService
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/ingest")

@router.post("/pdf")
async def ingest_pdf(file: UploadFile, current_user: dict = Depends(get_current_user)):
    pdf_bytes = await file.read()
    ids = PDFIngestService.ingest(pdf_bytes)
    return {"inserted": ids}
