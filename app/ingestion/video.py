from fastapi import APIRouter, UploadFile, File
from app.services.models import IngestResponse
from uuid import uuid4

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/video", response_model=IngestResponse)
async def ingest_video(file: UploadFile = File(...)):
    return await process_video(file)

async def process_video(file):
    source_id = str(uuid4())

    # TODO
    # Phase 1: just validate + store metadata
    # Phase 2: ffmpeg frames + ASR
    # Phase 3: Weaviate multi2vec

    return {
        "sourceId": source_id,
        "chunksCreated": 0,
        "status": "video accepted"
    }
