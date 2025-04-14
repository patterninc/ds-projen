"""Abstraction over the `pyproject.toml` file."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union

from projen import Component, DependencyType, Project, TomlFile


@dataclass
class PythonPackageMetadata:
    """Metadata for a Python package."""

    name: str
    description: str = "Add your description here"  # Default uv description
    version: str = "0.1.0"  # Default uv version
    requires_python: str = ">=3.11"
    dependencies: List[str] = field(default_factory=list)
    dev_dependencies: List[str] = field(default_factory=list)


class PyprojectToml(Component):
    """Abstraction over the `pyproject.toml` file."""

    def __init__(
        self,
        project: "Project",
        package_metadata: PythonPackageMetadata,
        file_path: Union[str, Path] = "pyproject.toml",
    ) -> None:
        super().__init__(project)
        self.__package_meta = package_metadata

        self._pyproject_toml_file = TomlFile(
            project=project,
            committed=True,
            file_path=str(file_path),
            readonly=True,
            marker=True,
            obj=get_pyproject_toml_values(package_meta=package_metadata),
        )

    def pre_synthesize(self) -> None:
        """Add dependencies to the project's shared Dependencies object reference."""
        for dep in self.__package_meta.dependencies:
            self.project.deps.add_dependency(spec=dep, type=DependencyType.RUNTIME)

        for dep in self.__package_meta.dev_dependencies:
            self.project.deps.add_dependency(spec=dep, type=DependencyType.DEVENV)

        return super().pre_synthesize()


def get_pyproject_toml_values(package_meta: PythonPackageMetadata) -> dict:
    """Construct the values to be written to the `pyproject.toml` file."""
    return {
        "project": {
            "name": package_meta.name,
            "version": package_meta.version,
            "description": package_meta.description,
            "readme": "README.md",
            "requires-python": package_meta.requires_python,
            "dependencies": package_meta.dependencies,
        },
        "dependency-groups": {
            "dev": package_meta.dev_dependencies,
        },
        "tool": {"pytest": {"ini_options": {"pythonpath": ["."]}}},
    }
