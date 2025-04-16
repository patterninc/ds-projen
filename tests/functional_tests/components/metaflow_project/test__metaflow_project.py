"""Test that can synth a projen repository."""

import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Generator

import pytest

from tests.consts import ARTIFACTS_DIR

REPO_NAME = "dummy-repo"
DOMAIN = "reference"
METAFLOW_PROJECT_NAME = "dummy-project"
METAFLOW_PROJECT_OUTDIR = f"domains/{DOMAIN}/{METAFLOW_PROJECT_NAME}"


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


@pytest.fixture(scope="function")
def repository_fpath() -> Generator[Path, None, None]:
    """Return the path of a temporary repository for testing purposes."""
    with tempfile.TemporaryDirectory(dir=ARTIFACTS_DIR) as tmp_dir:
        tmp_dir = Path(tmp_dir)  # noqa: PLW2901 `with` statement variable `tmp_dir` overwritten by assignment target

        # Create a .projenrc.py file in the temporary directory
        projenrc_content = dedent(f'''\
            from ds_projen import MetaflowProject, Repository

            repo = Repository(
                name="{REPO_NAME}",
            )

            project = MetaflowProject(
                repo=repo,
                name="{METAFLOW_PROJECT_NAME}",
                domain="{DOMAIN}",
            )

            project.add_flow("sample_flow.py")

            repo.synth()
            ''')

        projenrc_path = tmp_dir / ".projenrc.py"
        projenrc_path.write_text(projenrc_content)

        # Run projenrc.py to generate the project
        subprocess.run(
            ["uv", "run", ".projenrc.py"],
            cwd=str(tmp_dir),
            check=True,
        )

        yield tmp_dir


def test__sample_flow_finishes_successfully(repository_fpath: Path):
    """Test that the sample flow finishes successfully."""
    flow_dir = repository_fpath / f"{METAFLOW_PROJECT_OUTDIR}/src"
    flow_fpath = "sample_flow.py"

    # use subprocess to run the generated sample_flow.py and check that it finishes successfully
    subprocess.run(
        ["uv", "run", flow_fpath, "--environment=pypi", "--no-pylint", "run", "--tag=triggered-by-pytest"],
        cwd=str(flow_dir),
        check=True,
    )
