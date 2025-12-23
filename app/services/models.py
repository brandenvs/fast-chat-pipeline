from pydantic import BaseModel
from typing import Optional

class IngestResponse(BaseModel):
    chunks_created: int
    status: str





class ContextChunk(BaseModel):
    source_type: str
    content: str
    page: Optional[int] = None
    start_time_sec: Optional[float] = None
    end_time_sec: Optional[float] = None


    