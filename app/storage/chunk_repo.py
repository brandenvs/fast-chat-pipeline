# from typing import Iterable
# from services.models import ContextChunk
# from storage.db import get_db
# from uuid import uuid4


# EMBEDDING_MODEL = "text-embedding-3-small"


# async def save_chunks(source_id: str, source_type: str, chunks: Iterable[ContextChunk]) -> int:
#     if not chunks:
#         return 0

#     async with get_db() as conn:
#         # ensure source exists
#         await conn.execute(
#             """
#             INSERT INTO sources (id, source_type)
#             VALUES ($1, $2)
#             ON CONFLICT (id) DO NOTHING
#             """,
#             source_id,
#             source_type,
#         )

#         records = [
#             (
#                 uuid4(),
#                 source_id,
#                 source_type,
#                 c.content,
#                 c.page,
#                 c.start_time_sec,
#                 c.end_time_sec,
#             )
#             for c in chunks
#         ]

#         await conn.executemany(
#             """
#             INSERT INTO context_chunks (
#                 id,
#                 source_id,
#                 source_type,
#                 content,
#                 page_number,
#                 start_time_sec,
#                 end_time_sec,
#                 embedding
#             )
#             VALUES (
#                 $1,
#                 $2,
#                 $3,
#                 $4,
#                 $5,
#                 $6,
#                 $7,
#                 ai.embed($8, $4)
#             )
#             """,
#             [
#                 (*r, EMBEDDING_MODEL)
#                 for r in records
#             ],
#         )

#     return len(records)
