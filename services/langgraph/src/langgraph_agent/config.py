"""Configuration helpers for the LangGraph agent service."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime configuration loaded from environment variables."""

    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_provider: str = Field(default="openai", alias="DEFAULT_PROVIDER")
    fallback_provider: str = Field(default="ollama", alias="FALLBACK_PROVIDER")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="OPENAI_BASE_URL")
    openai_chat_model: str = Field(default="gpt-4o-mini", alias="OPENAI_CHAT_MODEL")
    ollama_base_url: str = Field(default="http://ollama:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="gpt-oss:20b", alias="OLLAMA_MODEL")
    mcp_registry_path: Path = Field(default=Path("/app/registry/registry.yaml"), alias="MCP_REGISTRY_PATH")

    class Config:
        populate_by_name = True
        extra = "ignore"

    def model_dump_env(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[arg-type]
