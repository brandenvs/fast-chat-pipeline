from typing import Any

from app.storage.weaviate import get_context
from app.services.chatgpt import generate_reply
from app.storage.chat_repo import get_session_messages, save_message


BASE_SYSTEM_PROMPT = """
You are a helpful assistant that prefers factual, grounded answers.

Rules:
- If relevant context is provided, you MUST base your answer strictly on that context.
- If the context clearly answers the question, do not add extra information.
- If the context does NOT contain the answer:
  - You MAY respond conversationally
  - Do NOT invent facts
  - Keep the response general, helpful, or clarifying
- If the user asks about something unrelated to any context, respond naturally as a chatbot.
- Never share considerations outside of the provided context.
- Keep responses concise and clear.
- Strip 
"""



async def handle_chat_message(session_id: str, textIn: str) -> dict[str, Any]:
    await save_message(session_id, "user", textIn)

    history = await get_session_messages(session_id)    
    conversation = [{"role": "system", "content": BASE_SYSTEM_PROMPT}] + history
    
    query = [textIn]    
    if len(history) >= 2:
        for msg in history[-4:]:
            if (msg["role"] == "user"):
                query.append(msg['content'])
    query.append(textIn)
    query.reverse()
    query_string = "\n".join(query)

    print('textIn ', textIn)
    print('query ', query_string)
    context = await get_context(query_string)
    print("\n\nCONTEXT:", context)

    if context:
        conversation.insert(
            1,
                {
                    "role": "system",
                    "content": f"""
                Use the following information to answer the user's question.

                {context}

                """,
                },
        )
    else:
        conversation.insert(
            1,
            {
                "role": "system",
                "content": """
    No relevant context was found! Do not respond to the user's question. Only keep the conversation flowing by asking the user more questions in order to get to a context hit.

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
