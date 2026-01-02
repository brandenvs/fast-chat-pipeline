from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import uuid4

from app.ingestion.llm_helper import generate_keywords_and_questions
from app.storage.weaviate import save_chunks
from app.ingestion.file_storage import save_uploaded_file
from app.ingestion.config import DOCUMENT_DIR
from app.ingestion.chunking import chunk_text
from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.document_extractor import extract_text_data
from app.services.models import ContextChunk, IngestResponse


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
    for idx, page in enumerate(data):
        print('PAGE ', idx)
        keywords, typical_questions = await generate_keywords_and_questions(page["text"])
        print('GENERATED KEYWORDS ', keywords)
        print('GENERATED TYPICAL QUESTIONS ', typical_questions)

        for chunk in chunk_text(page["text"]):
            chunks.append(
                ContextChunk(
                    source_id=uuid4().__str__(),
                    source_type=source_type,
                    content=chunk,
                    page_number=idx,
                    keywords=keywords,
                    typical_questions=typical_questions,
                )
            )
    total_saved = await save_chunks(chunks)
    try:
        if file_path.exists():
            file_path.unlink(missing_ok=True) # cleanup
    except Exception as ex:
        print("Cleanup failed:", ex)        
    return IngestResponse(
        chunks_created=total_saved,
        status=f"{ext} parsed",
    )

