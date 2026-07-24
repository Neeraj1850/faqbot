from fastapi import APIRouter, UploadFile, Depends
from app.services.pdf_ingest_service import PDFIngestService
from app.dependencies.api_key_auth import require_api_key

router = APIRouter(prefix="/ingest")

@router.post("/pdf")
async def ingest_pdf(file: UploadFile, auth=Depends(require_api_key)):
    pdf_bytes = await file.read()
    ids = PDFIngestService.ingest(pdf_bytes)
    return {"inserted": ids}
