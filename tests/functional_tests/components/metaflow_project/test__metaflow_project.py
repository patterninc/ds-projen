"""Test that can synth a projen repository."""

import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from ds_projen import MetaflowProject, Repository
from tests.consts import ARTIFACTS_DIR

DUMMY_REPO_NAME = "dummy-repo"
DUMMY_DOMAIN = "reference"
DUMMY_METAFLOW_PROJECT_NAME = "dummy-project"


@pytest.fixture(scope="function")
def repository_fpath() -> Generator[Path, None, None]:
    """Return the path of a temporary repository for testing purposes."""
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


def test__sample_flow_finishes_successfully(repository_fpath: Path):
    """Test that the sample flow finishes successfully."""
    flow_dir = repository_fpath / "domains" / DUMMY_DOMAIN / DUMMY_METAFLOW_PROJECT_NAME / "src"
    flow_fpath = "sample_flow.py"

    # use subprocess to run the generated sample_flow.py and check that it finishes successfully
    subprocess.run(
        ["uv", "run", flow_fpath, "--environment=pypi", "--no-pylint", "run"],
        cwd=flow_dir,
        check=True,
    )
