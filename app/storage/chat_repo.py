from typing import List, Dict
from storage.db import get_db

async def save_message(
    session_id: str,
    role: str,
    content: str,
):
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO chat_messages (session_id, role, content)
            VALUES (?, ?, ?)
            """,
            (session_id, role, content),
        )
        await db.commit()
        await db.close()

async def get_session_messages(
    session_id: str,
    limit: int = 50,
) -> List[Dict]:
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        await db.close()

    return [{"role": r[0], "content": r[1]} for r in rows]
