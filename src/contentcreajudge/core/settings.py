"""Centralized application settings loaded from environment variables."""

from __future__ import annotations

import os


class Settings:
    """Application settings with environment variable overrides."""

    # API / UI
    api_url: str = os.getenv("CONTENTCREAJUDGE_API_URL", "http://127.0.0.1:8000")
    env: str = os.getenv("CONTENTCREAJUDGE_ENV", "dev")
    log_level: str = os.getenv("CONTENTCREAJUDGE_LOG_LEVEL", "INFO")

    # SEO — semantic model
    seo_embedding_model: str = os.getenv(
        "SEO_EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    seo_semantic_top_k: int = int(os.getenv("SEO_SEMANTIC_TOP_K", "3"))
    seo_chunk_size: int = int(os.getenv("SEO_SEMANTIC_CHUNK_SIZE", "128"))
    seo_chunk_overlap: int = int(os.getenv("SEO_SEMANTIC_CHUNK_OVERLAP", "16"))


settings = Settings()
