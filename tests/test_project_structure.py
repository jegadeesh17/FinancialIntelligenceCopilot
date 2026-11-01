"""
Project structure checks: required files and directories exist.

Run: pytest tests/test_project_structure.py -v
"""

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def project_root() -> Path:
    return PROJECT_ROOT


class TestScaffoldStructure:
    """Verify scaffold files and directories exist."""

    @pytest.mark.parametrize(
        "relative_path",
        [
            "docs/PROJECT_SPEC.md",
            "docs/DECISIONS.md",
            "notebooks/FinancialIntelligenceCopilot.ipynb",
            "requirements.txt",
            ".env.example",
            "pytest.ini",
            "README.md",
            "src/.keep",
            "data/.keep",
        ],
    )
    def test_required_paths_exist(self, project_root: Path, relative_path: str):
        path = project_root / relative_path
        assert path.exists(), f"Missing required path: {relative_path}"
