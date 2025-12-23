# import aiosqlite
# from pathlib import Path
# from contextlib import asynccontextmanager
# import pgai

# DB_PATH = Path("chat.db")

# @asynccontextmanager
# async def get_db():
#     useSqlFile = False

#     if useSqlFile:
#         db = await aiosqlite.connect(DB_PATH)
#         try:
#             yield db
#         finally:
#             await db.close()
#     else:
#         pgai.install('postgres://postgres:password@127.0.0.1:5432/postgres')


# # 

import asyncpg
from contextlib import asynccontextmanager

DATABASE_URL = "postgres://postgres:postgres@127.0.0.1:5432/postgres"

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
