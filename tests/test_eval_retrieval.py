"""Unit tests for retrieval evaluation logic."""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestEvalRetrieval:
    def test_eval_questions_file_exists(self):
        path = PROJECT_ROOT / "data" / "eval_questions.json"
        assert path.exists()
        items = json.loads(path.read_text(encoding="utf-8"))
        assert len(items) >= 10

    def test_evaluate_with_mocked_retriever(self, monkeypatch):
        from scripts.eval_retrieval import evaluate
        from src.schemas import RetrievalResult

        monkeypatch.setattr("scripts.eval_retrieval.get_collection_count", lambda: 10)

        def fake_retrieve(question, top_k=5):  # noqa: ARG001
            if "KYC" in question or "kyc" in question.lower() or "capital" in question.lower():
                return [
                    RetrievalResult(
                        source="rbi_master_direction_kyc.pdf",
                        page=5,
                        text="KYC text",
                        chunk_index=0,
                        score=0.1,
                    )
                ]
            if "HDFC" in question or "deposit" in question.lower():
                return [
                    RetrievalResult(
                        source="hdfc_bank_annual_report.pdf",
                        page=10,
                        text="NII text",
                        chunk_index=0,
                        score=0.1,
                    )
                ]
            if "governance" in question.lower():
                return [
                    RetrievalResult(
                        source="sebi_lodr_governance.pdf",
                        page=2,
                        text="Governance text",
                        chunk_index=0,
                        score=0.1,
                    )
                ]
            if "SEBI" in question or "disclosure" in question.lower():
                return [
                    RetrievalResult(
                        source="sebi_circular_disclosure.pdf",
                        page=2,
                        text="LODR text",
                        chunk_index=0,
                        score=0.1,
                    )
                ]
            if "AML" in question or "money laundering" in question.lower():
                return [
                    RetrievalResult(
                        source="rbi_master_direction_aml.pdf",
                        page=3,
                        text="AML text",
                        chunk_index=0,
                        score=0.1,
                    )
                ]
            return []

        monkeypatch.setattr("scripts.eval_retrieval.retrieve", fake_retrieve)
        report = evaluate(top_k=3)
        assert report["total"] == 10
        assert report["hits"] >= 7
        assert report["hit_rate"] >= 0.70
