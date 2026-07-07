"""
Phase 6 checkpoint tests — Streamlit Chat UI.

Run: pytest tests/test_phase6_dashboard.py -v
"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestChatHelpers:
    def test_format_citations(self):
        from src.chat import format_citations
        from src.schemas import Citation

        text = format_citations([Citation(source="rbi.pdf", page=12)])
        assert "rbi.pdf" in text
        assert "p.12" in text

    def test_format_citations_empty(self):
        from src.chat import format_citations

        assert format_citations([]) == "Sources: none"

    def test_format_citations_groups_pages(self):
        from src.chat import format_citations
        from src.schemas import Citation

        text = format_citations(
            [
                Citation(source="rbi.pdf", page=12),
                Citation(source="rbi.pdf", page=14),
            ]
        )
        assert "rbi.pdf (p.12,14)" in text


class TestRagPipeline:
    def test_ask_question_wires_retriever_and_generator(self, monkeypatch):
        from src.schemas import Citation, RAGResponse, RetrievalResult

        def fake_retrieve(_q):
            return [RetrievalResult(source="rbi.pdf", page=10, text="KYC text", chunk_index=0, score=0.1)]

        def fake_generate(_q, contexts):
            assert len(contexts) == 1
            return RAGResponse(answer="Mock answer", citations=[Citation(source="rbi.pdf", page=10)], model="mock")

        monkeypatch.setattr("src.rag_pipeline.retrieve", fake_retrieve)
        monkeypatch.setattr("src.rag_pipeline.generate_answer", fake_generate)

        from src.rag_pipeline import ask_question

        result = ask_question("What are KYC requirements?")
        assert result.answer == "Mock answer"
        assert result.citations[0].source == "rbi.pdf"


class TestAppSmoke:
    def test_streamlit_app_renders(self):
        app_path = PROJECT_ROOT / "app" / "app.py"
        at = AppTest.from_file(str(app_path))
        at.run()
        assert not at.exception
        assert len(at.chat_message) >= 1

    @pytest.mark.integration
    def test_chat_roundtrip_with_mocked_pipeline(self, monkeypatch):
        from src.schemas import Citation, RAGResponse, RetrievalResult

        def fake_retrieve(_q, top_k=5, max_distance=None):  # noqa: ARG001
            return [RetrievalResult(source="doc.pdf", page=1, text="Some chunk", chunk_index=0, score=0.1)]

        def fake_generate(_q, _contexts):
            return RAGResponse(answer="Test response", citations=[Citation(source="doc.pdf", page=1)], model="mock")

        monkeypatch.setattr("src.retriever.retrieve", fake_retrieve)
        monkeypatch.setattr("src.generator.generate_answer", fake_generate)

        app_path = PROJECT_ROOT / "app" / "app.py"
        at = AppTest.from_file(str(app_path))
        at.run()
        at.chat_input[0].set_value("Hello").run()
        assert len(at.chat_message) >= 2
