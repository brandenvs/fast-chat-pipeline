from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    env: str = Field("development", env="ENV")

    class Config:
        env_file = "app/.env"
        env_file_encoding = "utf-8"


settings = Settings()

import os
import weaviate

WEAVIATE_HTTP_HOST = os.getenv("WEAVIATE_HTTP_HOST", "weaviate")
WEAVIATE_HTTP_PORT = int(os.getenv("WEAVIATE_HTTP_PORT", "8080"))
WEAVIATE_GRPC_HOST = os.getenv("WEAVIATE_GRPC_HOST", WEAVIATE_HTTP_HOST)
WEAVIATE_GRPC_PORT = int(os.getenv("WEAVIATE_GRPC_PORT", "50051"))

def weaviate_client():
    return weaviate.connect_to_custom(
        http_host=WEAVIATE_HTTP_HOST,
        http_port=WEAVIATE_HTTP_PORT,
        grpc_host=WEAVIATE_GRPC_HOST,
        grpc_port=WEAVIATE_GRPC_PORT,
    )
