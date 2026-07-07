"""Index metadata utilities for operational visibility."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import Settings, get_settings


def metadata_path(settings: Settings | None = None) -> Path:
    settings = settings or get_settings()
    return settings.chroma_path / "index_meta.json"


def write_index_metadata(
    chunk_count: int,
    pdf_count: int,
    settings: Settings | None = None,
) -> dict:
    settings = settings or get_settings()
    payload = {
        "last_indexed_at": datetime.now(timezone.utc).isoformat(),
        "chunk_count": int(chunk_count),
        "pdf_count": int(pdf_count),
        "embedding_model": settings.embedding_model,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
    }
    path = metadata_path(settings)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def read_index_metadata(settings: Settings | None = None) -> dict:
    path = metadata_path(settings)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
