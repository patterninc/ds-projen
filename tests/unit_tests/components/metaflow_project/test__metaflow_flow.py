"""Test that can synth a projen repository."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from ds_projen import MetaflowProject, Repository
from ds_projen.components.metaflow_project.metaflow_flow import get_flow_class_name_from_filepath
from tests.consts import ARTIFACTS_DIR

DUMMY_REPO_NAME = "dummy-repo"
DUMMY_DOMAIN = "reference"
DUMMY_METAFLOW_PROJECT_NAME = "dummy-project"


@pytest.fixture(scope="function")
def repository_with_metaflow_project() -> Generator[tuple[Repository, MetaflowProject], None, None]:
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

        yield repo, project


def test__flow_fname_ends_with__flow_dot_py(repository_with_metaflow_project: tuple[Repository, MetaflowProject]):
    _, project = repository_with_metaflow_project
    with pytest.raises(ValueError) as err:
        project.add_flow("dummy_flow")
        assert """Flow filenames must end with '_flow.py'.""" in str(err)


def test__flow_fname_is_a_importable_module_name(repository_with_metaflow_project: tuple[Repository, MetaflowProject]):
    _, project = repository_with_metaflow_project
    with pytest.raises(ValueError) as err:
        project.add_flow("@_flow.py")
        assert "Flow filenames must be a valid Python identifier." in str(err)


def test__flow_fname_is_lower_snake_case(repository_with_metaflow_project: tuple[Repository, MetaflowProject]):
    _, project = repository_with_metaflow_project
    with pytest.raises(ValueError) as err:
        project.add_flow("DummyFlow_flow.py")
        assert "Flow names must be lower snake case." in str(err)


def test__get_flow_class_name_from_filepath():
    """Test that the flow class name is extracted correctly from the file path."""
    assert get_flow_class_name_from_filepath("dummy_flow.py") == "DummyFlow"
    assert get_flow_class_name_from_filepath("some_example_flow.py") == "SomeExampleFlow"
