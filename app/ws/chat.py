from typing import Any

from services.chatgpt import generate_reply
from storage.chat_repo import get_session_messages, save_message


async def handle_chat_message(session_id: str, textIn: str) -> dict[str, Any]:
    await save_message(session_id, "user", textIn)

    history = await get_session_messages(session_id)
    conversation = (
        [{"role": "system", "content": "You are a concise, helpful assistant."}]
        + history
    )

    bot_reply = await generate_reply(conversation)
    await save_message(session_id, "assistant", bot_reply)

    return {
        "sessionId": session_id,
        "userMessage": textIn,
        "botReply": bot_reply,
        "previousMessages": history + [{"role": "assistant", "content": bot_reply}],
    }
