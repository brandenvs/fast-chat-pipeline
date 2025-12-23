from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import uuid4

from storage.weaviate import save_chunks
from ingestion.file_storage import save_uploaded_file
from ingestion.config import DOCUMENT_DIR
from ingestion.chunking import chunk_text
from ingestion.pdf_parser import parse_pdf
from ingestion.document_extractor import extract_text_data

from services.models import ContextChunk, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/document", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    try:
        return await process_document(file)
    except Exception as ex:
        print("DOCUMENT INGEST FAILED:", ex)
        raise HTTPException(status_code=500, detail="Document ingestion failed")


async def process_document(file: UploadFile) -> IngestResponse:
    source_type = "document"

    file_path = await save_uploaded_file(file, DOCUMENT_DIR)
    ext = file_path.suffix.lower()

    if ext == ".pdf":
        data = parse_pdf(file_path)
        data = [{"page": entry["page"], "text": entry["text"], "meta": {"unit": "pdf_page"}} for entry in data]
    else:
        data = extract_text_data(file_path)

    chunks: list[ContextChunk] = []
    for entry in data:
        for chunk in chunk_text(entry["text"]):
            if entry.get("page") is None:
                page_number = 1
            else:
                page_number = entry.get("page")
            print(chunk)
            chunks.append(
                ContextChunk(
                    source_type=source_type,
                    content=chunk,
                    page_number=page_number,
                )
            )
    saved = await save_chunks('document', chunks)
    try:
        if file_path.exists():
            file_path.unlink(missing_ok=True) # cleanup
    except Exception as ex:
        print("Cleanup failed:", ex)

    print(saved)
    return IngestResponse(
        chunks_created=saved,
        status=f"{ext} parsed",
    )
