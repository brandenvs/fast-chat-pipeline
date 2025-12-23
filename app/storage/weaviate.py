# services/weaviate.py
import json
from typing import Iterable
from uuid import uuid4

import weaviate
from weaviate.classes.query import Filter
from weaviate.classes.generate import GenerativeConfig

from services.models import ContextChunk
from storage.db import get_db


WEAVIATE_COLLECTION = "Context"


# INSERT / UPSERT CONTEXT
async def save_chunks(
    source_type: str,
    chunks: Iterable[ContextChunk],
) -> int:
    chunks = list(chunks)
    if not chunks:
        return 0

    # Generate IDs once
    records = [
        {
            "id": str(uuid4()),
            "source_type": source_type,
            "content": c.content,
            "page_number": c.page,
            "start_time_sec": c.start_time_sec,
            "end_time_sec": c.end_time_sec,
        }
        for c in chunks
    ]

    # ---- Weaviate insert ----
    with weaviate.connect_to_local() as client:
        collection = client.collections.use(WEAVIATE_COLLECTION)

        with collection.batch.fixed_size(batch_size=200) as batch:
            for r in records:
                batch.add_object(
                    uuid=r["id"],
                    properties={
                        "source_type": r["source_type"],
                        "content": r["content"],
                        "page_number": r["page_number"],
                        "start_time_sec": r["start_time_sec"],
                        "end_time_sec": r["end_time_sec"],
                    },
                )

    # ---- Postgres insert ----
    async with get_db() as conn:
        await conn.executemany(
            """
            INSERT INTO context_chunks (
                id,
                source_type,
                content,
                page_number,
                start_time_sec,
                end_time_sec
            )
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            [
                (
                    r["id"],
                    r["source_type"],
                    r["content"],
                    r["page_number"],
                    r["start_time_sec"],
                    r["end_time_sec"],
                )
                for r in records
            ],
        )

    return len(records)

def get_context(query: str):
    sematic_search_results = get_context_semantic(query)
    print('semantic result ', sematic_search_results)

    context_content = "\n\n".join(
        c["content"]
        for c in sematic_search_results
        if c.get("content") and c.get('distance') <= .49 # lower means better relevancy
    )
    return context_content
    if (context_content or context_content.strip() != ''): 
        return context_content
    else:
        rag_result = get_context_rag(query)
        return rag_result.get("content")


def get_context_semantic(query: str, limit: int = 5):
    with weaviate.connect_to_local() as client:
        collection = client.collections.use("Context")

        response = collection.generate.near_text(
            query=query,
            limit=limit,
            return_metadata=["distance"],
            grouped_task=(
                "Condense the information for a chatbot to quickly consume. "
                "Only include the condensed text."
            ),
        )

        return [
            {
                **obj.properties,
                "distance": obj.metadata.distance
            }
            for obj in response.objects
        ]



# RAG SEARCH (WITH LLM)
# def get_context_rag(query: str):
#     with weaviate.connect_to_local() as client:
#         collection = client.collections.use(WEAVIATE_COLLECTION)

#         response = collection.generate.near_text(
#             query=query,
#             limit=3,
#             # return_metadata=["distance"],
#             grouped_task="Condense the information for a chatbot to quickly consume. Only include the condensed text.",
#             generative_provider=GenerativeConfig.ollama(
#                 api_endpoint="http://ollama:11434",
#                 model="llama3.2",
#             ),
#         )

#         return response.generative.text

def get_context_rag(query: str):
    with weaviate.connect_to_local() as client:
        collection = client.collections.use(WEAVIATE_COLLECTION)

        response = collection.generate.near_text(
            query=query,
            limit=3,
            return_metadata=["distance"],
            grouped_task=(
                "Condense the information for a chatbot to quickly consume. "
                "Only include the condensed text."
            ),
            generative_provider=GenerativeConfig.ollama(
                api_endpoint="http://ollama:11434",
                model="llama3.2",
            ),
        )

        # Extract distances from retrieved objects
        distances = [
            obj.metadata.distance
            for obj in response.objects
            if obj.metadata and obj.metadata.distance is not None
        ]

        best_distance = min(distances) if distances else None

        return {
            "content": response.generative.text,
            "best_distance": best_distance,
            "distances": distances,
        }



# DELETE CONTEXT BY SOURCE TYPE
async def delete_context_by_source_type(source_type: str) -> int:
    deleted_weaviate = 0

    # ---- Weaviate delete ----
    with weaviate.connect_to_local() as client:
        collection = client.collections.use(WEAVIATE_COLLECTION)

        result = collection.data.delete_many(
            where=Filter.by_property("description").equal('My name is King Kong!')
        )

        deleted_weaviate = result.matches

    # ---- Postgres delete ----
    async with get_db() as conn:
        result = await conn.execute(
            """
            DELETE FROM context_chunks
            WHERE source_type = $1
            """,
            source_type,
        )

    return deleted_weaviate
