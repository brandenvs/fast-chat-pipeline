from typing import Any

from storage.weaviate import delete_context_by_source_type, get_context_semantic
from services.chatgpt import generate_reply
from storage.chat_repo import get_session_messages, save_message


BASE_SYSTEM_PROMPT = """
You are a context-bound assistant.

Rules:
- You may ONLY answer using the provided context.
- If the context does not contain the answer, reply with:
  "I don't have enough information to answer that."
- Do NOT use prior knowledge.
- Do NOT infer or guess.
- Keep answers concise and factual.
"""


async def handle_chat_message(session_id: str, textIn: str) -> dict[str, Any]:
    await save_message(session_id, "user", textIn)

    history = await get_session_messages(session_id)

    # conversation = (
    conversation = [{"role": "system", "content": BASE_SYSTEM_PROMPT}] + history

    # )

    embedding_results = get_context_semantic(textIn)

    context_content = "\n\n".join(
        c["content"]
        for c in embedding_results
        if c.get("content") and c.get('distance') < .25 # lower means better relevancy
    )
    print("context:", context_content)

    if context_content:
        conversation.insert(
            1, 
            {
                "role": "system",
                "content": f"""
    Context:
    {context_content}

    Use ONLY this context to answer the user.
    """,
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

