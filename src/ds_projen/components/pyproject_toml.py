"""Abstraction over the `pyproject.toml` file."""

from copy import deepcopy
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, Union

from projen import Component, Project, TomlFile
from tomlkit import dumps, parse

from ds_projen.components.metaflow_project.consts import REQUIRES_PYTHON


class PyprojectToml(Component):
    """Abstraction over the `pyproject.toml` file.

    This file is a bit unusual because it is "semi tamperproof".

    `projen synth` *will* overwrite this file just as it does with any tamperproof file, but

    1. the file is not read only
    2. because `uv add` needs to be able to modify it.

    So the `project.dependencies` and `dependency-groups` sections of the file can be
    freely modified.
    """

    def __init__(
        self,
        project: "Project",
        package_name: str,
        description: str,
        file_path: Union[str, Path] = "pyproject.toml",
        requires_python: str = REQUIRES_PYTHON,
        default_dependencies: list[str] | None = None,
    ) -> None:
        super().__init__(project)
        self.package_name = package_name
        self.description = description
        self.file_path = Path(file_path)

        default_dependencies = default_dependencies or []
        requires_python = requires_python or ">=3.9"

        # before projen replaces the old `pyproject.toml` (at synth time),
        # we read its original contents from disk so we can grab any dependencies
        # or dependency groups that the user may have manually added to `pyproject.toml`.
        # This way, we achieve a "semi tamperproof file", i.e. everything
        # in the file is locked down except `project.dependencies` and `dependency-groups`
        dependencies, dependency_groups = _try_get_deps_from_existing_pyproject_toml(
            pyproject_toml_fpath=self.file_path,
        )

        # on first synth, add these starter dependencies
        if not dependencies:
            dependencies = deepcopy(default_dependencies)

        contents: dict = get_pyproject_toml_values(
            package_name=self.package_name,
            description=self.description,
            dependencies=dependencies,
            dependency_groups=dependency_groups,
            requires_python=requires_python,
        )

        # Refer to these docs to see why we set this up the way we do:
        # https://github.com/projen/projen/blob/main/src/javascript/node-package.ts#L666-L671
        self.pyproject_toml_file = TomlFile(
            project=self.project,
            file_path=str(file_path),
            committed=True,
            marker=True,
            obj=contents,
            # we want `uv add` to work so the file can't be readonly; but projen will still overwrite it
            readonly=False,
        )


def _try_get_deps_from_existing_pyproject_toml(pyproject_toml_fpath: Path) -> tuple[list[str], dict[str, list[str]]]:
    dependencies: list[str] = []
    dependency_groups = deepcopy(DEFAULT_DEPENDENCY_GROUPS)

    if not pyproject_toml_fpath.exists():
        return dependencies, dependency_groups

    # if it exists: add any deps found in pyproject.toml to the default deps
    pyproject_toml_contents: dict = read_toml(pyproject_toml_fpath)

    if "project" in pyproject_toml_contents and "dependencies" in pyproject_toml_contents["project"]:
        pyproj_deps = pyproject_toml_contents["project"]["dependencies"]

        # NOTE: this attempt to merge the default deps and pyproject.toml deps
        # will not work if versions are pinned. That's okay. The user can figure
        # that out or we can refactor this merge logic later.
        #
        # NOTE: the list is sorted since the order of list(some_set) is not deterministic.
        # We need the order to be stable so that running `projen synth` does not cause
        # the file to be modified (and therefore the build to fail).
        dependencies = sorted(list(set(pyproj_deps) | set(dependencies)))

    if "dependency-groups" in pyproject_toml_contents:
        for group_name, deps in pyproject_toml_contents["dependency-groups"].items():
            if group_name in dependency_groups:
                pyproj_dep_group = dependency_groups[group_name]
                dependency_groups[group_name] = sorted(list(set(pyproj_dep_group) | set(deps)))
            else:
                dependency_groups[group_name] = sorted(deps)

    return dependencies, dependency_groups


def get_pyproject_toml_values(
    package_name: str,
    description: str,
    dependencies: list[str],
    dependency_groups: dict[str, list[str]],
    requires_python: str,
) -> dict:
    """Construct the values to be written to the `pyproject.toml` file."""
    return {
        "project": {
            "name": package_name,
            # version is required in order to `pip install` the metaflow folder
            # as a package, which is useful for testing. But we aren't using the
            # version for anything else, e.g. git tags or publishing to PyPI, so we
            # fix it to 0.0.0. Later on, we may make more use of this and actually bump it.
            "version": "0.0.0",
            "description": description,
            "readme": "README.md",
            "requires-python": requires_python,
            "dependencies": deepcopy(dependencies),
        },
        "dependency-groups": deepcopy(dependency_groups),
        "tool": {
            **deepcopy(PYTEST_TOOL_SETTINGS),
            **deepcopy(PYTEST_COV_TOOL_SETTINGS),
            **get_poe_tasks(),
        },
        "build-system": {
            "build-backend": "hatchling.build",
            "requires": ["hatchling"],
        },
    }


def read_toml(toml_fpath: Path) -> Dict[str, Any]:
    """Read the contents of the TOML file and parse as dict."""
    return parse(toml_fpath.read_text(encoding="utf-8"))


def to_toml(d: Dict[str, Any]) -> str:
    """Return a TOML string representation of the dict."""
    return dumps(d)


DEFAULT_DEPENDENCY_GROUPS = {
    "dev": ["pytest", "pytest-cov", "pre-commit", "ruff", "mypy"],
}

PYTEST_TOOL_SETTINGS = {
    "pytest": {
        "ini_options": {
            "markers": [
                "slow: marks tests as slow (deselect with '-m \"not slow\"')",
            ],
            "pythonpath": ["."],
            "addopts": [
                # unit test report which can be consumed by tools like codecov
                "--junitxml=test-reports/report.xml",
                # coverage (from pytest-cov); the pytest-cov settings send these reports into test-reports/
                "--cov=src",
                "--cov-report=xml",
                "--cov-report=html",
                "--cov-report=term",
            ],
        },
    },
}

PYTEST_COV_TOOL_SETTINGS = {
    "coverage": {
        # Specifies the source paths for coverage analysis
        "paths": {"source": ["src/"]},
        "report": {
            # Patterns to exclude from coverage reporting
            # These lines generally can never be executed, e.g.
            # 'if TYPE_CHECKING:', so they should not be counted
            # against the total coverage score
            "exclude_also": [
                "pragma: no cover",
                "if False",
                "def __repr__",
                "if self.debug",
                "raise AssertionError",
                "raise NotImplementedError",
                "raise MemoryError",
                "except DistributionNotFound",
                "except ImportError",
                "@abc.abstractmethod",
                "if 0:",
                "if __name__ == .__main__.:",
                "if typing.TYPE_CHECKING:",
                "if TYPE_CHECKING:",
            ],
            # Files or directories to omit from coverage analysis
            "omit": ["tests/artifacts/*"],
            # Whether to show lines missing coverage in the report
            "show_missing": True,
        },
        # Enable branch coverage analysis
        "run": {"branch": True},
        # File path for the XML coverage report; tools like
        # codecov and coveralls can typically integrate with GitHub actions
        # and use this file to generate an HTML view of coverage that
        # people can look at during PRs
        "xml": {"output": "test-reports/coverage.xml"},
        # Directory where the HTML coverage report will be saved
        "html": {"directory": "test-reports/htmlcov"},
        # File path for the JSON coverage report
        "json": {"output": "test-reports/coverage.json"},
    }
}


def get_poe_tasks() -> dict:
    """Return tasks that can be executed with `poe <task_name>`."""
    return {
        "poe": {
            "tasks": {
                "lint": {
                    "cmd": "pre-commit run --all-files",
                    "help": "Run linting, formatting, projen synth, and other static code quality tools",
                },
                "test": {
                    "cmd": "pytest",
                    "help": "Run all tests",
                },
                "serve-coverage-report": {
                    "help": "Serve the coverage report on http://localhost:3333",
                    "shell": dedent("""\
                        echo "Serving coverage report on http://localhost:3333"
                        echo "Press Ctrl+C to stop the server"
                        
                        python -m http.server 3333 --directory ./test-reports/htmlcov
                        """),
                },
                "clean": {
                    "help": "Remove all files generated by tests, builds, or operating this codebase",
                    "shell": dedent("""\
                        rm -rf dist build coverage.xml test-reports sample/

                        find . \\
                            -type d \\
                            \\( \\
                            -name "*cache*" \\
                            -o -name "*.dist-info" \\
                            -o -name "*.egg-info" \\
                            -o -name "*htmlcov" \\
                            -o -name "*.metaflow" \\
                            -o -name "*.metaflow.s3" \\
                            -o -name "*.mypy_cache" \\
                            -o -name "*.pytest_cache" \\
                            -o -name "*.ruff_cache" \\
                            -o -name "*__pycache__" \\
                            \\) \\
                            -not -path "*env/*" \\
                            -exec rm -r {} + || true

                        find . \\
                            -type f \\
                            -name "*.pyc" \\
                            -o -name "*.DS_Store" \\
                            -o -name "*.coverage" \\
                            -not -path "*env/*" \\
                            -exec rm {} +
                        """),
                },
            }
        }
    }
