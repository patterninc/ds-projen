"""Constant values to be imported by test files."""

from pathlib import Path

TESTS_DIR = Path(__file__).parent  # tests/ directory
PROJECT_DIR = (TESTS_DIR / "../").resolve()  # ds-projen/ directory
ARTIFACTS_DIR = TESTS_DIR / "artifacts"
