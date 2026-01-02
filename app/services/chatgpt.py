import os
from typing import List, Dict

from openai import AsyncOpenAI
from app.core.settings import settings

def get_openai_client():
    return AsyncOpenAI(api_key=settings.openai_api_key)


async def generate_reply(messages: List[Dict[str, str]]) -> str:
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content
