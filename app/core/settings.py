from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    env: str = Field("development", env="ENV")

    class Config:
        env_file = "app/.env"
        env_file_encoding = "utf-8"


settings = Settings()
