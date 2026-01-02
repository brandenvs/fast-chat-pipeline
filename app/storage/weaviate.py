import re
from typing import Dict, Iterable, List
import weaviate
from weaviate.classes.query import MetadataQuery
from app.core.settings import weaviate_client
from app.services.models import ContextChunk
from app.storage.db_helper import insert_context_chunks
import httpx
from typing import Optional

# CONTEXT INSERTS

async def save_chunks(incoming_chunks: Iterable[ContextChunk]) -> int:
    create_chunks = list(incoming_chunks)
    if not create_chunks:
        return 0

    # Weaviate insert
    with weaviate_client() as client:
        collection = client.collections.use("Context")
        with collection.batch.fixed_size(batch_size=200) as batch:
            for chunk in create_chunks:
                batch.add_object(
                    uuid=chunk.source_id,
                    properties={
                        "source_type": chunk.source_type,
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "keywords": chunk.keywords,
                        "typical_questions": chunk.typical_questions,
                    },
                )
    # Postgres insert
    await insert_context_chunks(create_chunks)
    return len(create_chunks)

# HELPERS

def is_weak_query(query: str) -> bool:
    tokens = query.strip().split()
    return len(tokens) < 4 or len(query) < 30

def get_chunk_content(chunk) -> str:
    if isinstance(chunk, dict):
        return chunk.get("content", "")
    return getattr(chunk, "content", "")

def normalize_text(text: str) -> str:
    text = text.replace("\u2019", "'").replace("\u2014", "-")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def merge_texts(base: str, addition: str) -> str:
    if not base:
        return addition
    max_overlap = min(len(base), len(addition))
    for i in range(max_overlap, 50, -1):
        if base.endswith(addition[:i]):
            return base + addition[i:]
    return base + "\n\n" + addition

def build_context_string(chunks: list) -> str:
    context = ""
    for chunk in chunks:
        content = normalize_text(get_chunk_content(chunk))
        if not content:
            continue
        context = merge_texts(context, content)
    return context.strip()

def build_context_with_metadata(chunks: list) -> str:
    keywords = sorted({
        kw for c in chunks for kw in (c.keywords if hasattr(c, "keywords") else c.get("keywords", []))
    })
    body = build_context_string(chunks)
    return f"""SOURCE: document
KEYWORDS: {", ".join(keywords)}

CONTENT:
{body}
"""

# LLM HELPERS

# async def generate_ollama(
#     prompt: str,
#     model: str = 'llama3.2',
#     system: Optional[str] = None,
#     temperature: float = 0.3,
#     max_tokens: int = 512,
#     timeout: int = 30,
# ) -> str:
#     payload = {
#         "model": model,
#         "prompt": prompt,
#         "stream": False,
#         "options": {
#             "temperature": temperature,
#             "num_predict": max_tokens,
#         },
#     }

#     if system:
#         payload["system"] = system

#     async with httpx.AsyncClient(timeout=timeout) as client:
#         res = await client.post(
#             "http://ollama:11434/api/generate",
#             json={
#                 "model": "llama3.2",
#                 "prompt": prompt,
#                 "stream": False,
#                 "options": {
#                     "temperature": temperature,
#                     "num_predict": max_tokens
#                 }
#             }
#         )
#         res.raise_for_status()

#     data = res.json()
#     return data.get("response", "").strip()

async def generate_ollama(
    prompt: str,
    model: str = "llama3.2",
    system: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 512,
    timeout: int = 30,
) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.post(f"http://ollama:11434/v1/chat/completions", json=payload)

        if res.status_code >= 400:
            print("Ollama error:", res.status_code, res.text)

        res.raise_for_status()

    data = res.json()
    return (data["choices"][0]["message"]["content"] or "").strip()

async def expand_query(query: str) -> str:
    prompt = f"""
You are rewriting a user search query to slightly strengthen it for semantic search.

STRICT RULES:
- Do NOT add placeholders
- Do NOT invent ages, locations, names, or examples
- Do NOT ask questions
- Do NOT change the meaning
- ONLY add minimal connector or stop words if needed
- Keep it ONE sentence
- Output ONLY the rewritten query

Original query:
"{query}"

Rewritten query:
"""
    expanded = await generate_ollama(
        prompt,
        temperature=0.1,
        max_tokens=48,
    )
    return expanded.strip() or query


# CONTEXT RETRIEVAL

async def get_context(query: str) -> str:
    weak = is_weak_query(query)
    print("IS WEAK QUERY: ", weak)

    chunks: List[Dict] = []

    if weak:
        query = await expand_query(query)
        print('EXPANDED QUERY ', query)
        
        # Keyword / hybrid path
        result = keyword_search(query, limit=8)

        for obj in result.objects:
            print("CHUNK META", obj.metadata)
            props = obj.properties or {}
            print("CHUNK KEYWORDS", props.get("keywords", []))

            if obj.metadata.score and obj.metadata.score >= 0.4:
                chunks.append({
                    "content": props.get("content", ""),
                    "keywords": props.get("keywords", []),
                    "source_type": props.get("source_type", "document"),
                    "page_number": props.get("page_number", 0),
                    "typical_questions": props.get("typical_questions", []),
                })

    else:
        # Semantic path
        semantic_chunks = get_context_semantic_quick(query, limit=5)

        for obj in semantic_chunks.objects:
            print("CHUNK META", obj.metadata)
            props = obj.properties or {}
            print("CHUNK KEYWORDS", props.get("keywords", []))

            if obj.metadata.distance and obj.metadata.distance <= 0.45:
                chunks.append({
                    "content": props.get("content", ""),
                    "keywords": props.get("keywords", []),
                    "source_type": props.get("source_type", "document"),
                    "page_number": props.get("page_number", 0),
                    "typical_questions": props.get("typical_questions", []),
                })

    if not chunks:
        return ""

    return build_context_string(chunks)

def keyword_search(query: str, limit: int = 5):
    with weaviate_client() as client:
        collection = client.collections.use("Context")
        response = collection.query.bm25(
            query=query,
            limit=limit,
            query_properties=["keywords^2", "typical_questions", "content"],
            return_metadata=MetadataQuery(score=True),
        )
        return response

def get_context_semantic_quick(query: str, limit: int = 5):
    with weaviate_client() as client:
        collection = client.collections.use("Context")
        response = collection.query.near_text(
            query=query,
            limit=limit,
            return_metadata=MetadataQuery(distance=True)
        )
        return response


import weaviate
from weaviate.classes.config import Property, DataType, Configure

def init_weaviate(client: weaviate.WeaviateClient) -> None:
    existing = {c.name for c in client.collections.list_all().values()}

    if "Context" in existing:
        client.collections.delete("Context")
        existing = {c.name for c in client.collections.list_all().values()}

    if "Context" in existing:
        return

    client.collections.create(
        name="Context",
        properties=[
            Property(name="source_type", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="page_number", data_type=DataType.INT),
            Property(name="keywords", data_type=DataType.TEXT_ARRAY),
            Property(name="typical_questions", data_type=DataType.TEXT_ARRAY),
        ],
        vectorizer_config=Configure.Vectorizer.text2vec_ollama(
            api_endpoint="http://ollama:11434",
            model="nomic-embed-text",
        ),
    )
