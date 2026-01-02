import shutil
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from app.ingestion.config import DOCUMENT_DIR

async def save_uploaded_file(
    file: UploadFile,
    base_dir: Path
) -> Path:
    base_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid4().hex
    ext = Path(file.filename).suffix.lower()
    dest = base_dir / f"{file_id}{ext}"

    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    await file.close() 
    return dest
