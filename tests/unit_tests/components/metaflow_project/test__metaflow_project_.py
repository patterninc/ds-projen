"""Test that can synth a projen repository."""

import tempfile
from pathlib import Path

import pytest
import yaml

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


def get_workflow_contents(repository_fpath: Path) -> dict:
    """Test that the Metaflow CI/CD workflow file exists and return its content."""
    workflow_name = f"ci-cd--{TEST_DOMAIN}--{TEST_METAFLOW_PROJECT_NAME}.yml"
    workflow_file = repository_fpath / ".github" / "workflows" / workflow_name
    assert workflow_file.exists(), f"Expected workflow file {workflow_file} does not exist"

    # Use BaseLoader instead of safe_load to prevent YAML from interpreting unquoted keys
    # like "on" as booleans(True)

    # YAML indicates boolean values with the keywords True, On and Yes for true.
    # False is indicated with False, Off, or No.
    workflow_content: dict = yaml.load(
        workflow_file.read_text(encoding="utf-8"),
        Loader=yaml.BaseLoader,
    )
    return workflow_content


@pytest.mark.parametrize(
    "expected_file_suffix",
    [
        # github actions
        str(Path(".github", "workflows", f"ci-cd--{TEST_DOMAIN}--{TEST_METAFLOW_PROJECT_NAME}.yml")),
        # project files
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "README.md")),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "pyproject.toml")),
        # src dir
        str(
            Path(
                "domains",
                TEST_DOMAIN,
                TEST_METAFLOW_PROJECT_NAME,
                "src",
                TEST_METAFLOW_PROJECT_NAME.replace("-", "_"),
                "__init__.py",
            )
        ),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "src", "sample_flow.py")),
        # tests
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "tests", "fixtures", "__init__.py")),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "tests", "fixtures", "general_fixtures.py")),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "tests", "unit_tests", "__init__.py")),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "tests", "unit_tests", "test__sample.py")),
        str(Path("domains", TEST_DOMAIN, TEST_METAFLOW_PROJECT_NAME, "tests", "conftest.py")),
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
    workflow_triggers: dict = workflow_content["on"]

    expected_paths = {
        f"domains/{TEST_DOMAIN}/{TEST_METAFLOW_PROJECT_NAME}/**",
        f".github/workflows/ci-cd--{TEST_DOMAIN}--{TEST_METAFLOW_PROJECT_NAME}.yml",
    }
    assert set(workflow_triggers["push"]["paths"]) == expected_paths
    assert set(workflow_triggers["pull_request"]["paths"]) == expected_paths
