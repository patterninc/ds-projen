"""Abstraction over a README file."""

from pathlib import Path

from projen import Component, Project

from ds_projen.components.lazy_sample_file import LazySampleFile


class Readme(Component):
    """Abstraction over a README file."""

    def __init__(
        self,
        project: "Project",
        package_name: str,
        file_path: str | Path = "README.md",
    ) -> None:
        super().__init__(project)
        self.file_path = Path(file_path)

        # Create a simple README file with optional content
        self.readme_file = LazySampleFile(
            project=project,
            file_path=str(file_path),
            get_contents_fn=lambda: f"# {package_name}\n",
        )
