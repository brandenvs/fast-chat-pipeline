from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from ingestion.chunking import chunk_text
from ingestion.config import IMAGE_DIR
from ingestion.file_storage import save_uploaded_file
from ingestion.ocr_helper import infer_ocr
from storage.chunk_repo import save_chunks
from ingestion.models import ContextChunk, IngestResponse
from uuid import uuid4

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/image", response_model=IngestResponse)
async def ingest_image(file: UploadFile = File(...)):
    return await process_image(file)

async def process_image(file):
    try:
        source_id = str(uuid4())
        source_type = "image"

        file_path = await save_uploaded_file(file, IMAGE_DIR)
        data = infer_ocr(file_path)
        print(data)

        chunks: list[ContextChunk] = []
        for chunk in chunk_text(data):
            chunks.append(
                ContextChunk(
                    sourceId=source_id,
                    sourceType=source_type,
                    content=chunk,
                )
            )
        saved = await save_chunks(chunks)
    finally:
        # cleanup
        if file_path and Path(file_path).exists():
            Path(file_path).unlink(missing_ok=True)
    return IngestResponse(
        sourceId=source_id,
        chunksCreated=saved,
        status="document parsed",
    )