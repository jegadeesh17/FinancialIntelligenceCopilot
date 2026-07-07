"""Simple query logging for audit and debugging."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src.config import PROJECT_ROOT

LOG_DIR = PROJECT_ROOT / "logs"
QUERY_LOG = LOG_DIR / "query_log.jsonl"


def log_query(
    question: str,
    top_sources: list[str],
    fallback_used: bool,
    latency_ms: float,
) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "top_sources": top_sources,
        "fallback_used": bool(fallback_used),
        "latency_ms": round(float(latency_ms), 2),
    }
    with QUERY_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
