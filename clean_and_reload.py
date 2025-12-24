"""
⚠️  DANGER ZONE
This script will DELETE ALL CONTEXT DATA
- Weaviate vectors
- Postgres chat + chunk tables

Run manually only.
"""

import asyncio
import weaviate
from weaviate.classes.config import Configure, Property, DataType
import asyncpg
import os

POSTGRES_DSN = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/postgres",
)

WEAVIATE_OLLAMA_ENDPOINT = "http://ollama:11434"
WEAVIATE_COLLECTION = "Context"

POSTGRES_TABLES = [
    "context_chunks",
    "chat_messages",
]

# POSTGRES WIPE
async def wipe_postgres():
    print("Wiping Postgres tables...")
    conn = await asyncpg.connect(POSTGRES_DSN)

    try:
        for table in POSTGRES_TABLES:
            print(f" - TRUNCATE {table}")
            await conn.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
    finally:
        await conn.close()

    print(">> Postgres wiped")


def wipe_weaviate():
    print("Wiping Weaviate collection...")

    with weaviate.connect_to_local() as client:
        # Delete collection if exists
        try:
            client.collections.delete(WEAVIATE_COLLECTION)
            print(f" - Deleted collection {WEAVIATE_COLLECTION}")
        except Exception:
            print(" - Collection did not exist")

        client.collections.create(
            name="Context",
            properties=[
                Property(name="source_type", data_type=DataType.TEXT),
                Property(name="content", data_type=DataType.TEXT),
                Property(name="page_number", data_type=DataType.INT),
                Property(name="keywords", data_type=DataType.TEXT_ARRAY),
                Property(name="typical_questions", data_type=DataType.TEXT_ARRAY),
            ],
            vector_config=Configure.Vectors.text2vec_ollama(
                api_endpoint="http://ollama:11434",
                model="nomic-embed-text",
            ),
            generative_config=Configure.Generative.ollama(
                api_endpoint="http://ollama:11434",
                model="llama3.2",
            ),
        )


    print(">> Weaviate reset")



async def main():
    print("\nTHIS WILL DELETE ALL DATA\n")
    wipe_weaviate()
    await wipe_postgres()
    print("\nFULL WIPE COMPLETE\n")

if __name__ == "__main__":
    asyncio.run(main())
