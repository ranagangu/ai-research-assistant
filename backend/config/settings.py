import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Research Assistant"
    SECRET_KEY: str = "a52f5273-dd0a-47af-b13c-a2089be0f6ed-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database & Storage
    DATABASE_URL: str = "sqlite:///./research_assistant.db"
    CHROMA_DB_DIR: str = "./chroma_db"
    UPLOAD_DIR: str = "./uploads"

    # AI Configurations
    DEFAULT_LLM_PROVIDER: str = "openrouter"
    DEFAULT_LLM_MODEL: str = "meta-llama/llama-3-8b-instruct"
    DEFAULT_EMBEDDING_PROVIDER: str = "openrouter"
    DEFAULT_EMBEDDING_MODEL: str = "openai/text-embedding-3-small"

    # API Keys
    OPENROUTER_API_KEY:str

    # Pydantic Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


