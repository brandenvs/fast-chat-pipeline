import aiosqlite
from pathlib import Path
from contextlib import asynccontextmanager
import pgai

DB_PATH = Path("chat.db")

@asynccontextmanager
async def get_db():
    useSqlFile = False

    if useSqlFile:
        db = await aiosqlite.connect(DB_PATH)
        try:
            yield db
        finally:
            await db.close()
    else:
        pgai.install(DB_URL)


