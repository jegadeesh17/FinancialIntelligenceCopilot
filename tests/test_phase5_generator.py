"""
Phase 5 checkpoint tests — LLM Generator.

Run: pytest tests/test_phase5_generator.py -v
Integration: pytest tests/test_phase5_generator.py -m integration -v
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def settings():
    sys.path.insert(0, str(PROJECT_ROOT))
    if "src.config" in sys.modules:
        importlib.reload(sys.modules["src.config"])
    from src.config import Settings

    return Settings()


@pytest.fixture
def contexts():
    from src.schemas import RetrievalResult

    return [
        RetrievalResult(
            source="rbi_master_direction_kyc.pdf",
            page=12,
            chunk_index=0,
            text="Banks shall collect proof of identity and proof of address under KYC norms.",
            score=0.12,
        ),
        RetrievalResult(
            source="sebi_circular_disclosure.pdf",
            page=2,
            chunk_index=0,
            text="Listed entities must comply with disclosure obligations under SEBI LODR regulations.",
            score=0.21,
        ),
    ]


class TestGenerator:
    def test_build_prompt_contains_question_and_context(self, contexts):
        from src.generator import build_prompt

        prompt = build_prompt("What are KYC requirements?", contexts)
        assert "Question: What are KYC requirements?" in prompt
        assert "rbi_master_direction_kyc.pdf" in prompt
        assert "Page: 12" in prompt

    def test_generate_answer_no_context_returns_guardrail(self, settings):
        from src.generator import generate_answer

        result = generate_answer("Any question", [], settings=settings)
        assert "could not find relevant context" in result.answer.lower()
        assert result.citations == []

    def test_generate_answer_with_mocked_llm(self, contexts, settings, monkeypatch):
        from src.generator import generate_answer

        def fake_call(_prompt, settings):  # noqa: ARG001
            return "KYC requires proof of identity and address."

        monkeypatch.setattr("src.generator._call_openrouter", fake_call)
        result = generate_answer("What are KYC requirements?", contexts, settings=settings)

        assert "KYC" in result.answer
        assert len(result.citations) == 2
        assert result.citations[0].source == "rbi_master_direction_kyc.pdf"

    def test_generate_answer_empty_question(self, contexts, settings):
        from src.generator import generate_answer

        result = generate_answer("   ", contexts, settings=settings)
        assert "non-empty question" in result.answer.lower()


@pytest.mark.integration
class TestGeneratorIntegration:
    def test_openrouter_live_if_key_available(self, contexts, settings):
        from src.generator import generate_answer

        if not settings.openrouter_api_key or settings.openrouter_api_key.startswith("sk-or-v1-your"):
            pytest.skip("OPENROUTER_API_KEY not set for integration test")

        result = generate_answer("What are KYC requirements?", contexts, settings=settings)
        assert len(result.answer) > 0
        assert len(result.citations) >= 1
