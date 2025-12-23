from typing import Any

from storage.weaviate import delete_context_by_source_type, get_context_semantic
from services.chatgpt import generate_reply
from storage.chat_repo import get_session_messages, save_message


async def handle_chat_message(session_id: str, textIn: str) -> dict[str, Any]:
    await save_message(session_id, "user", textIn)

    history = await get_session_messages(session_id)

    conversation = (
        [{"role": "system", "content": "You are a concise, helpful chat bot."}]
        + history
    )

    embedding_results = get_context_semantic(textIn)

    context_content = "\n\n".join(
        c["content"]
        for c in embedding_results
        if c.get("content") and c.get('distance') < .50 # lower means better relevancy
    )
    print("context:", context_content)

    if context_content:
        conversation.insert(
            0,
            {
                "role": "system",
                "content": f"Relevant context:\n{context_content}\nIMPORTANT NOTE: GENERATE PLAIN TEXT and DO NOT GENERATE MARKDOWN",
            },
        )

    bot_reply = await generate_reply(conversation)

    await save_message(session_id, "assistant", bot_reply)

    return {
        "sessionId": session_id,
        "userMessage": textIn,
        "botReply": bot_reply,
        "previousMessages": history + [{"role": "assistant", "content": bot_reply}],
    }

