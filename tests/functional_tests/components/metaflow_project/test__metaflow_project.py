"""Test that can synth a projen repository."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from ds_projen import MetaflowProject, Repository

THIS_DIR = Path(__file__).parent
TESTS_DIR = (THIS_DIR / "../").resolve()
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
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


def test__sample_flow_finishes_successfully(repository_fpath: Path):
    """Test that the sample flow finishes successfully."""
    flow_dir = repository_fpath / "domains" / DUMMY_DOMAIN / DUMMY_METAFLOW_PROJECT_NAME / "src"
    flow_fpath = "sample_flow.py"

    # use subprocess to run `uv run sample_flow.py`
    # and check that it finishes successfully
    subprocess.run(["uv", "run", str(flow_fpath)], cwd=flow_dir, check=True)
