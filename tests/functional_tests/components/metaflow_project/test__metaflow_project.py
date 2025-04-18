"""Test that can synth a projen repository."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from ds_projen import MetaflowProject, Repository
from tests.consts import ARTIFACTS_DIR, TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, TEST_REPO_NAME


@pytest.fixture(scope="function")
def repository_fpath() -> Path:
    """Return the path of a temporary repository for testing purposes."""
    with tempfile.TemporaryDirectory(dir=ARTIFACTS_DIR) as tmp_dir:
        tmp_dir = Path(tmp_dir)

        repo = Repository(
            name=TEST_REPO_NAME,
            outdir=str(tmp_dir / TEST_REPO_NAME),
        )

        project = MetaflowProject(
            repo=repo,
            name=TEST_METAFLOW_PROJECT_NAME,
            domain=TEST_DOMAIN,
        )

        project.add_flow("sample_flow.py")

        repo.synth()
        yield tmp_dir / TEST_REPO_NAME


def test__sample_flow_finishes_successfully(repository_fpath: Path):
    """Test that the sample flow finishes successfully."""
    flow_dir = repository_fpath / "domains" / TEST_DOMAIN / TEST_METAFLOW_PROJECT_NAME / "src"
    flow_fpath = "sample_flow.py"

    # create a .metaflowconfig/config_local.json file
    (repository_fpath / ".metaflowconfig").mkdir(exist_ok=True)
    (repository_fpath / ".metaflowconfig" / "config_local.json").write_text("{}")

    # use subprocess to run `uv run sample_flow.py` and check that it finishes successfully
    # https://docs.outerbounds.com/use-multiple-metaflow-configs/
    subprocess.run(
        ["uv", "run", flow_fpath, "--environment=pypi", "--no-pylint", "run", "--tag=triggered-by-pytest"],
        cwd=flow_dir,
        check=True,
        env=os.environ.copy()
        | {
            "METAFLOW_HOME": str(repository_fpath / ".metaflowconfig"),
            "METAFLOW_PROFILE": "local",
        },
    )
