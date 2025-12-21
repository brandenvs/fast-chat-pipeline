import aiosqlite
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # app/
DB_PATH = BASE_DIR / "chat.db"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
print(SCHEMA_PATH)
async def init_db():
    if not SCHEMA_PATH.exists():
        raise RuntimeError(f"Schema file not found: {SCHEMA_PATH}")

    async with aiosqlite.connect(DB_PATH) as db:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        await db.executescript(schema)
        await db.commit()
