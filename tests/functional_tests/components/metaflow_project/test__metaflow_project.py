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


"""
fix: use .projenrc.py file for synthesizing the repo & project instead directly within the test fixture

Problem:
Direct Python invocation of Repository/MetaflowProject was creating the project directory,
`domains/reference/dummy-project/src/dummy_project/__init__.py`, relative to the test execution
directory, aka, the root of "ds-projen" project, when we do `uv run pytest tests/`

```
ds-projen
|── domains/reference/dummy-project/src/dummy_project/__init__.py
├── src
│   └── ds_projen/
├── tests/
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
├── run
└── uv.lock
```

Solution:
Generate and run .projenrc.py file in temporary directory and do `uv run .projenrc.py` to synthesize the project.
This way:
- Correct path resolution relative to project root
- And doing this way matches real-world usage pattern of ds-projen

Test now successfully creates and runs metaflow project in correct location.
"""


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

    # create a .metaflowconfig/config_local.json file
    (repository_fpath / ".metaflowconfig").mkdir(exist_ok=True)
    (repository_fpath / ".metaflowconfig" / "config_local.json").write_text("{}")

    # use subprocess to run `uv run sample_flow.py`
    # and check that it finishes successfully
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
