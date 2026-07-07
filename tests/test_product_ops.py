from pathlib import Path


def test_index_metadata_roundtrip(tmp_path):
    from src.config import Settings
    from src.indexing import read_index_metadata, write_index_metadata

    settings = Settings(chroma_persist_dir=str(tmp_path))
    payload = write_index_metadata(chunk_count=123, pdf_count=3, settings=settings)
    loaded = read_index_metadata(settings=settings)
    assert loaded["chunk_count"] == 123
    assert loaded["pdf_count"] == 3
    assert loaded["embedding_model"] == settings.embedding_model
    assert "last_indexed_at" in payload


def test_query_log_written(tmp_path, monkeypatch):
    from src import telemetry

    monkeypatch.setattr(telemetry, "LOG_DIR", tmp_path)
    monkeypatch.setattr(telemetry, "QUERY_LOG", tmp_path / "query_log.jsonl")

    telemetry.log_query(
        question="What is KYC?",
        top_sources=["rbi.pdf"],
        fallback_used=False,
        latency_ms=123.4,
    )
    assert telemetry.QUERY_LOG.exists()
    content = telemetry.QUERY_LOG.read_text(encoding="utf-8")
    assert "What is KYC?" in content
    assert "rbi.pdf" in content
