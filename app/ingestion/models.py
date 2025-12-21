from pydantic import BaseModel
from typing import Optional

class IngestResponse(BaseModel):
    sourceId: str
    chunksCreated: int
    status: str


class ContextChunk(BaseModel):
    sourceId: str
    sourceType: str
    content: str
    page: Optional[int] = None