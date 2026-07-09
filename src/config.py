"""Central configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = Field(default="openrouter", description="LLM provider")
    openrouter_api_key: str = Field(default="", description="OpenRouter API key")
    openrouter_model: str = Field(
        default="openrouter/free",
        description="Model slug on OpenRouter",
    )
    llm_max_retries: int = Field(default=3, ge=1, le=5)
    openrouter_fallback_models: str = Field(
        default="",
        description="Comma-separated fallback OpenRouter model slugs.",
    )

    chroma_persist_dir: str = Field(
        default="data/chroma_db",
        description="ChromaDB persistence directory",
    )
    raw_pdf_dir: str = Field(
        default="data/raw_pdfs",
        description="Directory containing source PDF files",
    )
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model id",
    )
    chunk_size: int = Field(default=800, ge=200, le=4000)
    chunk_overlap: int = Field(default=100, ge=0, le=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    low_confidence_distance: float = Field(
        default=0.85,
        ge=0.0,
        le=2.0,
        description="If best retrieval distance is above this threshold, flag low confidence.",
    )
    api_key: str = Field(default="", description="Optional API key for FastAPI endpoints.")
    api_rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        le=1000,
        description="Max API requests per minute per IP for /ask.",
    )

    @field_validator("chunk_overlap")
    @classmethod
    def overlap_less_than_chunk_size(cls, v: int, info) -> int:
        chunk_size = info.data.get("chunk_size", 800)
        if v >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return v

    @property
    def fallback_models(self) -> list[str]:
        return [m.strip() for m in self.openrouter_fallback_models.split(",") if m.strip()]

    @property
    def chroma_path(self) -> Path:
        path = Path(self.chroma_persist_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path

    @property
    def raw_pdf_path(self) -> Path:
        path = Path(self.raw_pdf_dir)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
