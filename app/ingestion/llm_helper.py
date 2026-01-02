import httpx
from typing import Tuple, List
import json
import re


async def generate_keywords_and_questions(text: str) -> Tuple[List[str], List[str]]:
    prompt = f"""
Return ONLY valid JSON.

Format:
{{
  "keywords": ["string"],
  "questions": ["string"]
}}

Rules:
- No markdown
- No explanation
- No trailing text

Text:
{text}
"""

    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "http://ollama:11434/v1/chat/completions",
            json={
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": "You are a strict JSON generator."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 300,
                "stream": False,
            },
        )
        res.raise_for_status()
        data = res.json()

    raw = (data.get("choices", [{}])[0].get("message", {}) or {}).get("content", "") or ""
    parsed = extract_json_object(raw)

    if not parsed:
        print("Invalid JSON from LLM")
        return [], []
    return validate_llm_payload(parsed)


def extract_json_object(text: str) -> dict | None:
    match = re.search(r"\{[\s\S]*\}", text)  # remove noise in json response
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def validate_llm_payload(data: dict) -> tuple[list[str], list[str]]:
    if not isinstance(data, dict):
        return [], []
    keywords = data.get("keywords", [])
    questions = data.get("questions", [])
    if not isinstance(keywords, list):
        keywords = []
    if not isinstance(questions, list):
        questions = []
    return keywords, questions
