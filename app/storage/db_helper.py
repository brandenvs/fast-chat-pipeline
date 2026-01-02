import asyncpg
from contextlib import asynccontextmanager
from typing import List
from app.services.models import ContextChunk


DATABASE_URL = "postgres://postgres:postgres@db:5432/postgres"
_pool: asyncpg.Pool | None = None

async def init_db():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=10,
        )

@asynccontextmanager
async def get_db():
    if _pool is None:
        raise RuntimeError("DB not initialized")

    async with _pool.acquire() as conn:
        yield conn

async def insert_context_chunks(chunks: List[ContextChunk]):
    async with get_db() as conn:
        await conn.executemany(
            """
            INSERT INTO context_chunks (
                source_id,
                source_type,
                content,
                page_number,
                keywords,
                typical_questions
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            [
                (
                    chunk.source_id,
                    chunk.source_type,
                    chunk.content,
                    chunk.page_number,
                    ", ".join(chunk.keywords),
                    "\n- ".join(chunk.typical_questions),
                )
                for chunk in chunks
            ],
        )
