from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from uuid import uuid4

from ingestion.chunking import chunk_text
from ingestion.config import IMAGE_DIR
from ingestion.file_storage import save_uploaded_file
from ingestion.ocr_helper import infer_ocr
from storage.weaviate import save_chunks

from services.models import ContextChunk, IngestResponse

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/image", response_model=IngestResponse)
async def ingest_image(file: UploadFile = File(...)):
    return await process_image(file)


async def process_image(file: UploadFile) -> IngestResponse:
    source_type = "image"

    file_path: Path | None = None
    try:
        # Save image
        file_path = await save_uploaded_file(file, IMAGE_DIR)

        # OCR image → text
        text = infer_ocr(file_path)

        if not text or len(text.strip()) < 30:
            return IngestResponse(
                chunks_created=0,
                status="image ignored (no meaningful text)",
            )

        # Chunk OCR text
        chunks: list[ContextChunk] = []
        for chunk in chunk_text(text):
            if len(chunk.strip()) < 30:
                continue

            chunks.append(
                ContextChunk(
                    content=chunk,
                    source_type='image',
                    page=None,
                    start_time_sec=None,
                    end_time_sec=None,
                )
            )

        saved = await save_chunks(source_type, chunks)

        return IngestResponse(
            chunks_created=saved,
            status="image parsed",
        )

    finally:
        # Cleanup
        if file_path and file_path.exists():
            file_path.unlink(missing_ok=True)
