"""Test that can synth a projen repository."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from ds_projen import MetaflowProject, Repository
from tests.consts import ARTIFACTS_DIR

# REPO_NAME = "dummy-repo"
# DOMAIN = "reference"
# METAFLOW_PROJECT_NAME = "dummy-project"
# METAFLOW_PROJECT_OUTDIR = f"domains/{DOMAIN}/{METAFLOW_PROJECT_NAME}"

DUMMY_REPO_NAME = "dummy-repo"
DUMMY_DOMAIN = "reference"
DUMMY_METAFLOW_PROJECT_NAME = "dummy-project"


@pytest.fixture(scope="function")
def repository_fpath() -> Path:
    """Return the path of a temporary repository for testing purposes."""
    ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)

    with tempfile.TemporaryDirectory(dir=ARTIFACTS_DIR) as tmp_dir:
        tmp_dir = Path(tmp_dir)

        repo = Repository(
            name=DUMMY_REPO_NAME,
            outdir=str(tmp_dir / DUMMY_REPO_NAME),
        )

        project = MetaflowProject(
            repo=repo,
            name=DUMMY_METAFLOW_PROJECT_NAME,
            domain=DUMMY_DOMAIN,
        )

        project.add_flow("sample_flow.py")

        repo.synth()
        yield tmp_dir / DUMMY_REPO_NAME


def test__all_expected_files_exist(repository_fpath: Path):
    """Test that all expected files exist in the repository."""
    project_dir = repository_fpath / "domains" / DUMMY_DOMAIN / DUMMY_METAFLOW_PROJECT_NAME
    expected_files = [
        project_dir / "README.md",
        project_dir / "pyproject.toml",
        project_dir / "src" / DUMMY_METAFLOW_PROJECT_NAME.replace("-", "_") / "__init__.py",
        project_dir / "src" / "sample_flow.py",
        # tests
        project_dir / "tests" / "fixtures" / "__init__.py",
        project_dir / "tests" / "fixtures" / "general_fixtures.py",
        project_dir / "tests" / "unit_tests" / "__init__.py",
        project_dir / "tests" / "unit_tests" / "test__sample.py",
        project_dir / "tests" / "conftest.py",
    ]

    for fpath in expected_files:
        assert fpath.exists()
