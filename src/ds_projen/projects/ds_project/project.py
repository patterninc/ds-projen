import re
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from projen import Component

from ds_projen.components.lazy_sample_file import LazySampleFile
from ds_projen.components.pyproject_toml import PyprojectToml, PythonPackageMetadata
from ds_projen.components.readme import Readme

if TYPE_CHECKING:
    from ds_projen.projects.repository.project import Repository


class MetaflowProject(Component):
    """A pre-configured Metaflow project."""

    def __init__(  # noqa: PLR0913  # Too many arguments in function definition
        self,
        repo: "Repository",
        *,
        name: str,
        description: str,
        import_module_name: str | None = None,
        version: str = "0.1.0",  # uv defaults to 0.1.0
        domain: Annotated["Domain", "Allowed DS Domains"] | str | None = None,
        dependencies: list[str] | None = None,
        dev_dependencies: list[str] | None = None,
        outdir: Path | str | None = None,
        requires_python: str = ">=3.11",
    ) -> None:
        """Initialize a new Python package project.

        :param name: This is the name of your project. Default: $BASEDIR
        
        :param import_module_name: Name of the python package as used in imports and filenames. \
            Must only consist of alphabetic characters and underscores. \
            Defaults to project name with hyphens replaced by underscores.
        
        :param version: semantic version of the package; will be the version in PyPI
        :param description: brief description of what the package does.
        
        :param dependencies: List of runtime dependencies for this project. \
            Dependencies may use the format: ``<module>@<semver>`` or standard ``pip`` format, e.g. ``pandas>=1, <2`` \
            Additional dependencies can be added via ``project.add_dependency()``.
        
        :param outdir: The root directory of the project. Relative to this directory, all files are synthesized. \
            If this project has a parent, this directory is relative to the parent directory and it cannot be the \
            same as the parent or any of it's other sub-projects. Default: "."
        
        :param parent: The parent project, if this project is part of a bigger project.
        """
        super().__init__(repo)

        if domain:
            self.outdir = Path("domains") / validate_domain(domain).value / (outdir or name)
        else:
            # Default to the root directory if no domain is provided
            self.outdir = Path(outdir or name)

        self.repo: "Repository" = repo
        self.name = validate_project_name(name)
        self.import_module_name = (
            validate_import_module_name(import_module_name) if import_module_name else self.name.replace("-", "_")
        )
        self.package_dir = self.outdir / self.import_module_name

        # register self as project on the parent directory
        repo.metaflow_projects.append(self)

        self.init_py = LazySampleFile(
            self.repo,
            file_path=(self.package_dir / "__init__.py").resolve(),
            get_contents_fn=lambda: f'"""Module for {self.name}"""\n',
        )

        self.pyproject_toml = PyprojectToml(
            project=self.repo,
            file_path=self.outdir / "pyproject.toml",
            package_metadata=PythonPackageMetadata(
                name=self.name,
                version=version,
                description=description,
                requires_python=requires_python,
                dependencies=dependencies or [],
                dev_dependencies=dev_dependencies or [],
            ),
        )

        self.readme = Readme(
            project=self.repo,
            package_name=self.name,
            file_path=self.outdir / "README.md",
        )


class Domain(str, Enum):
    """Domains for Pattern Data Science Monorepo."""

    CONTENT = "content"
    ADVERTISING = "advertising"
    DEMAND_GENERATION = "demand-generation"
    FORECASTING = "forecasting"
    MARKET_INTELLIGENCE = "market-intelligence"
    OPERATIONS = "operations"
    ADVISIORY = "advisory"

    @classmethod
    def list_domains(cls) -> list[str]:
        """List all available domains."""
        return [domain.value for domain in cls]


def validate_domain(domain: str | Domain) -> Domain:
    """Validate the domain string and convert it to a Domain enum."""
    try:
        if isinstance(domain, Domain):
            return domain

        return Domain(domain)
    except ValueError as e:
        raise ValueError(f"Invalid domain: {domain}. Must be one of {Domain.list_domains()}.") from e


def validate_project_name(name: str) -> str:
    """Validate and normalize project name.

    Rules:
    - Only lowercase letters and hyphens as logical seperators allowed, e.g. "my-project"
    - Must start and end with a letter
    - Converts to lowercase automatically
    """
    name = name.lower().strip()

    # TODO: Regex can be improved, write tests for it
    pattern = r"^[a-z][a-z-]*[a-z]$"
    if not re.match(pattern, name):
        raise ValueError(
            "Project name must:\n- Only contain lowercase letters and hyphens\n- Start and end with a letter"
        )

    return name


def validate_import_module_name(name: str) -> str:
    """Validate and normalize import module name.

    Rules:
    - Only lowercase letters and underscores as logical separators allowed, e.g. "my_project"
    - Must start and end with a letter
    - No hyphens (not valid in Python module names)
    - Converts to lowercase automatically
    """
    name = name.lower().strip()

    # TODO: Regex can be improved, write tests for it
    pattern = r"^[a-z][a-z_]*[a-z]$"
    if not re.match(pattern, name):
        raise ValueError(
            "Import module name must:\n- Only contain lowercase letters and underscores\n- Start and end with a letter"
        )

    return name
