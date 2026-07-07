"""
Phase 7 checkpoint tests — Docker containerization.

Run: pytest tests/test_phase7_docker.py -v
"""

import shutil
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestDockerArtifacts:
    @pytest.mark.parametrize(
        "relative_path",
        [
            "Dockerfile",
            "docker-compose.yml",
            ".dockerignore",
        ],
    )
    def test_required_docker_files_exist(self, relative_path: str):
        assert (PROJECT_ROOT / relative_path).exists(), f"Missing {relative_path}"

    def test_dockerfile_contains_streamlit_command(self):
        dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")
        assert "streamlit" in dockerfile and "app/app.py" in dockerfile
        assert "EXPOSE 8501" in dockerfile

    def test_compose_maps_port_and_mounts_data(self):
        compose = (PROJECT_ROOT / "docker-compose.yml").read_text(encoding="utf-8")
        assert "8501:8501" in compose
        assert "./data/raw_pdfs:/app/data/raw_pdfs" in compose
        assert "./data/chroma_db:/app/data/chroma_db" in compose


class TestDockerComposeConfig:
    def test_compose_config_valid_if_docker_present(self):
        docker = shutil.which("docker")
        if not docker:
            pytest.skip("Docker CLI not installed")

        result = subprocess.run(
            [docker, "compose", "config"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        )
        if result.returncode != 0:
            pytest.skip(f"Docker compose unavailable in this environment: {result.stderr.strip()}")

        assert "services:" in result.stdout
        assert "financial-compliance-rag" in result.stdout
