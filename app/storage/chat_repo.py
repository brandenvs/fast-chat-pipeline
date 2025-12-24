from typing import List, Dict
from storage.db_helper import get_db


async def save_message(session_id: str, role: str, content: str) -> None:
    async with get_db() as conn:
        await conn.execute(
            """
            INSERT INTO chat_messages (session_id, role, content)
            VALUES ($1, $2, $3)
            """,
            session_id,
            role,
            content,
        )

async def get_session_messages(session_id: str, limit: int = 50) -> List[Dict]:
    async with get_db() as conn:
        rows = await conn.fetch(
            """
            SELECT role, content
            FROM chat_messages
            WHERE session_id = $1
            ORDER BY created_at ASC
            LIMIT $2
            """,
            session_id,
            limit,
        )
    return [{"role": r["role"], "content": r["content"]} for r in rows]
