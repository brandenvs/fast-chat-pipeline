from pydantic import BaseModel

class IngestResponse(BaseModel):
    chunks_created: int
    status: str

class ContextChunk(BaseModel):
    source_id: str
    source_type: str
    content: str
    page_number: int = 0
    keywords: list[str] = []
    typical_questions: list[str] = []
