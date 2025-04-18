"""Test that can synth a projen repository."""

import tempfile
from pathlib import Path

import pytest
import yaml

from ds_projen import MetaflowProject, Repository
from tests.consts import ARTIFACTS_DIR

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

        # while True:
        #     ...

        yield tmp_dir / DUMMY_REPO_NAME


def get_workflow_contents(repository_fpath: Path) -> dict:
    """Test that the Metaflow CI/CD workflow file exists and return its content."""
    workflow_name = f"ci-cd--{DUMMY_DOMAIN}--{DUMMY_METAFLOW_PROJECT_NAME}.yml"
    workflow_file = repository_fpath / ".github" / "workflows" / workflow_name
    assert workflow_file.exists(), f"Expected workflow file {workflow_file} does not exist"

    workflow_content: dict = yaml.safe_load(workflow_file.read_text(encoding="utf-8"))

    return workflow_content


@pytest.mark.parametrize(
    "expected_file_suffix",
    [
        # github actions
        str(Path(".github", "workflows", f"ci-cd--{DUMMY_DOMAIN}--{DUMMY_METAFLOW_PROJECT_NAME}.yml")),
        # project files
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "README.md")),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "pyproject.toml")),
        # src dir
        str(
            Path(
                "domains",
                DUMMY_DOMAIN,
                DUMMY_METAFLOW_PROJECT_NAME,
                "src",
                DUMMY_METAFLOW_PROJECT_NAME.replace("-", "_"),
                "__init__.py",
            )
        ),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "src", "sample_flow.py")),
        # tests
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "tests", "fixtures", "__init__.py")),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "tests", "fixtures", "general_fixtures.py")),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "tests", "unit_tests", "__init__.py")),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "tests", "unit_tests", "test__sample.py")),
        str(Path("domains", DUMMY_DOMAIN, DUMMY_METAFLOW_PROJECT_NAME, "tests", "conftest.py")),
    ],
)
def test__all_expected_files_exist(repository_fpath: Path, expected_file_suffix: str):
    """Test that all expected files exist in the repository."""
    fpath = repository_fpath / expected_file_suffix
    assert fpath.exists()


@pytest.mark.parametrize(
    "expected_job",
    [
        # project-level jobs
        "lint",
        "test",
        "manual-deploy",
        # flow-specific jobs
        "auto-deploy--sample_flow_py",
    ],
)
def test__expected_jobs_are_generated_into_the_github_actions_workflow(repository_fpath: Path, expected_job: str):
    """Test that the Metaflow CI/CD workflow contains expected jobs."""
    workflow_content = get_workflow_contents(repository_fpath)

    jobs: dict = workflow_content["jobs"]
    assert len(jobs) == 4
    assert expected_job in jobs.keys()


def test__metaflow_ci_cd_workflow_triggers(repository_fpath: Path):
    """Test that the Metaflow CI/CD workflow has correct trigger paths."""
    workflow_content = get_workflow_contents(repository_fpath)

    from rich import print

    print(workflow_content.keys())

    workflow_triggers: dict = workflow_content["on"]

    expected_paths = {
        f"domains/{DUMMY_DOMAIN}/{DUMMY_METAFLOW_PROJECT_NAME}/**",
        f".github/workflows/ci-cd--{DUMMY_DOMAIN}--{DUMMY_METAFLOW_PROJECT_NAME}.yml",
    }
    assert set(workflow_triggers["push"]["paths"]) == expected_paths
    assert set(workflow_triggers["pull_request"]["paths"]) == expected_paths
