"""Constant values to be imported by test files."""

from pathlib import Path

TESTS_DIR = Path(__file__).parent  # tests/
PROJECT_DIR = (TESTS_DIR / "../").resolve()  # ds-projen/
ARTIFACTS_DIR = TESTS_DIR / "artifacts"

# Constants for synting a test project
TEST_REPO_NAME = "test-repo"
TEST_METAFLOW_PROJECT_NAME = "test-project"
TEST_DOMAIN = "reference"
