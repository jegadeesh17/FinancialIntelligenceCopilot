"""Tests for FastAPI endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(monkeypatch):
    from src.schemas import Citation, RAGResponse, RetrievalResult
    from src.config import Settings

    def fake_retrieve(_q, top_k=None, max_distance=None, **kwargs):  # noqa: ARG001
        return [
            RetrievalResult(
                source="rbi_master_direction_kyc.pdf",
                page=12,
                text="KYC requires proof of identity and address.",
                chunk_index=0,
                score=0.12,
                document_category="regulatory",
            )
        ]

    def fake_generate(_q, contexts):
        assert len(contexts) >= 1
        return RAGResponse(
            answer="Banks must collect proof of identity and address.",
            citations=[Citation(source="rbi_master_direction_kyc.pdf", page=12)],
            model="mock-model",
        )

    def fake_count(**kwargs):  # noqa: ARG001
        return 42

    monkeypatch.setattr("api.main.retrieve", fake_retrieve)
    monkeypatch.setattr("api.main.generate_answer", fake_generate)
    monkeypatch.setattr("api.main.get_collection_count", fake_count)
    monkeypatch.setattr("api.main.read_index_metadata", lambda: {"pdf_count": 3})
    monkeypatch.setattr("api.main.get_settings", lambda: Settings())

    from api.main import _request_buckets, app

    _request_buckets.clear()

    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"
        assert body["chunk_count"] == 42


class TestAskEndpoint:
    def test_ask_returns_grounded_response(self, client):
        response = client.post("/ask", json={"question": "What are KYC requirements?"})
        assert response.status_code == 200
        body = response.json()
        assert "identity" in body["answer"].lower()
        assert body["citations"][0]["source"] == "rbi_master_direction_kyc.pdf"
        assert body["source_chunks"][0]["page"] == 12
        assert body["model"] == "mock-model"
        assert body["low_confidence"] is False
        assert isinstance(body["best_score"], float)
        assert body["source_chunks"][0]["document_category"] == "regulatory"

    def test_ask_rejects_empty_question(self, client):
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422

    def test_ask_rejects_missing_question(self, client):
        response = client.post("/ask", json={})
        assert response.status_code == 422

    def test_ask_requires_api_key_when_configured(self, client, monkeypatch):
        from src.config import Settings
        from api.main import _request_buckets

        monkeypatch.setattr("api.main.get_settings", lambda: Settings(api_key="secret-key"))
        _request_buckets.clear()

        response = client.post("/ask", json={"question": "What are KYC requirements?"})
        assert response.status_code == 401

        response = client.post(
            "/ask",
            json={"question": "What are KYC requirements?"},
            headers={"x-api-key": "secret-key"},
        )
        assert response.status_code == 200

    def test_ask_rate_limit_returns_429(self, client, monkeypatch):
        from src.config import Settings
        from api.main import _request_buckets

        monkeypatch.setattr("api.main.get_settings", lambda: Settings(api_rate_limit_per_minute=1))
        _request_buckets.clear()

        first = client.post("/ask", json={"question": "What are KYC requirements?"})
        second = client.post("/ask", json={"question": "What are KYC requirements?"})
        assert first.status_code == 200
        assert second.status_code == 429
