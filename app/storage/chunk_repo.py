import aiosqlite
from pathlib import Path
from typing import Iterable
from ingestion.models import ContextChunk
from storage.db import get_db

async def save_chunks(chunks: Iterable[ContextChunk]) -> int:
    count = 0
    async with get_db() as db:
        await db.executemany(
            """
            INSERT INTO document_chunks
              (source_id, source_type, content, page)
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    c.sourceId,
                    c.sourceType,
                    c.content,
                    c.page,
                )
                for c in chunks
            ],
        )
        await db.commit()
        count = len(list(chunks))

    return count
