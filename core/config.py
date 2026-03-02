# core/config.py

import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# IMPORTANT: Load .env before reading environment variables
load_dotenv()


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://resdb_chqu_user:yWppCmyXMl8LGJAaYbbzSh5RUYPQSGjW@dpg-d6amt9gboq4c73dgdr20-a.oregon-postgres.render.com/resdb_chqu"

    available_models: list[str] = [
    "openai/gpt-4-turbo",
    "openai/gpt-4o",
    "anthropic/claude-sonnet-4",
    "deepseek/deepseek-chat",
    "google/gemini-2.0-flash-exp",
    "cohere/command-a-03-2025"
]

    # LLM
    cohere_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_model: str = "openai/gpt-4-turbo"

    # Auth (REQUIRED)
    jwt_secret_key: str

    # Environment
    environment: str = "development"

    class Config:
        extra = "ignore"


# Directly instantiate (no manual overrides needed)
config = Settings()