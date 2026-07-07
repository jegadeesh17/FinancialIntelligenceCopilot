"""Tests for FastAPI endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(monkeypatch):
    from src.schemas import Citation, RAGResponse, RetrievalResult

    def fake_retrieve(_q, top_k=None, max_distance=None, **kwargs):  # noqa: ARG001
        return [
            RetrievalResult(
                source="rbi_master_direction_kyc.pdf",
                page=12,
                text="KYC requires proof of identity and address.",
                chunk_index=0,
                score=0.12,
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

    from api.main import app

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

    def test_ask_rejects_empty_question(self, client):
        response = client.post("/ask", json={"question": ""})
        assert response.status_code == 422

    def test_ask_rejects_missing_question(self, client):
        response = client.post("/ask", json={})
        assert response.status_code == 422
