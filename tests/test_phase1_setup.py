"""
Phase 1 checkpoint tests — Project Setup & MLOps Foundation.

Run: pytest tests/test_phase1_setup.py -v
"""

import importlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"


@pytest.fixture(scope="module")
def project_root() -> Path:
    return PROJECT_ROOT


class TestProjectStructure:
    """Verify Phase 1 scaffold and config files exist."""

    @pytest.mark.parametrize(
        "relative_path",
        [
            "src/config.py",
            "app/app.py",
            "requirements.txt",
            ".env.example",
            "pytest.ini",
            "README.md",
            "docs/PROJECT_SPEC.md",
            "docs/DATA_SOURCES.md",
            "notebooks/FinancialIntelligenceCopilot.ipynb",
        ],
    )
    def test_required_files_exist(self, project_root: Path, relative_path: str):
        path = project_root / relative_path
        assert path.exists(), f"Missing required file: {relative_path}"


class TestDependenciesImportable:
    """Verify pinned packages can be imported (after pip install)."""

    @pytest.mark.parametrize(
        "module_name",
        [
            "dotenv",
            "pydantic",
            "pydantic_settings",
            "httpx",
            "streamlit",
            "pytest",
        ],
    )
    def test_core_package_importable(self, module_name: str):
        importlib.import_module(module_name)

    @pytest.mark.parametrize(
        "module_name",
        [
            "fitz",
            "chromadb",
            "sentence_transformers",
        ],
    )
    def test_rag_package_importable(self, module_name: str):
        importlib.import_module(module_name)


class TestConfig:
    """Verify settings module loads and has expected RAG fields."""

    def test_settings_loads_with_defaults(self):
        sys.path.insert(0, str(SRC.parent))
        if "src.config" in sys.modules:
            importlib.reload(sys.modules["src.config"])
        from src.config import Settings

        settings = Settings(_env_file=None)
        assert settings.llm_provider == "openrouter"
        assert settings.openrouter_model == "openrouter/free"
        assert settings.embedding_model == "sentence-transformers/all-MiniLM-L6-v2"
        assert settings.chunk_size == 800
        assert settings.chunk_overlap == 100
        assert settings.top_k == 5
        assert settings.llm_max_retries == 3

    def test_path_properties_resolve_under_project_root(self):
        from src.config import Settings

        settings = Settings()
        assert settings.chroma_path == PROJECT_ROOT / "data" / "chroma_db"
        assert settings.raw_pdf_path == PROJECT_ROOT / "data" / "raw_pdfs"

    def test_chunk_overlap_validation(self):
        from pydantic import ValidationError
        from src.config import Settings

        with pytest.raises(ValidationError):
            Settings(chunk_size=500, chunk_overlap=500)
