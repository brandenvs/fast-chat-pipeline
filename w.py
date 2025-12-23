import weaviate
from weaviate.classes.config import Configure, Property, DataType


with weaviate.connect_to_local() as client:
    client.collections.delete("Context")

    client.collections.create(
        name="Context",
        properties=[
            Property(name="source_type", data_type=DataType.TEXT),
            Property(name="content", data_type=DataType.TEXT),
            Property(name="page_number", data_type=DataType.INT),
            Property(name="start_time_sec", data_type=DataType.NUMBER),
            Property(name="end_time_sec", data_type=DataType.NUMBER),
        ],
        vector_config=Configure.Vectors.text2vec_ollama(
            api_endpoint="http://ollama:11434",
            model="nomic-embed-text",
        ),
)
