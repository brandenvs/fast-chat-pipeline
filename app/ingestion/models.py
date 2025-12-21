from pydantic import BaseModel
from typing import Optional

class IngestResponse(BaseModel):
    sourceId: str
    chunksCreated: int
    status: str


class ContextChunk(BaseModel):
    content: str
    page: Optional[int] = None
    start_time_sec: Optional[float] = None
    end_time_sec: Optional[float] = None


    