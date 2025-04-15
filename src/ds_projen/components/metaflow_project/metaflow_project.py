"""A pre-configured Metaflow project."""

import re
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from projen import Component

from ds_projen.components.lazy_sample_file import LazySampleFile
from ds_projen.components.metaflow_project.ci_cd_github_actions_workflow import (
    MetaflowProjectCiCdGitHubActionsWorkflow,
)
from ds_projen.components.metaflow_project.consts import DATA_SCIENCE_DOMAINS, TDataScienceDomain
from ds_projen.components.metaflow_project.metaflow_flow import MetaflowFlow
from ds_projen.components.pyproject_toml import PyprojectToml
from ds_projen.components.readme import Readme

if TYPE_CHECKING:
    from ds_projen.projects.repository.repository import Repository


class MetaflowProject(Component):
    """A pre-configured Metaflow project belonging to one of the data science domains."""

    def __init__(  # noqa: PLR0913  # Too many arguments in function definition
        self,
        repo: "Repository",
        *,
        name: str,
        domain: TDataScienceDomain,
        import_module_name: str | None = None,
        outdir: Path | str | None = None,
    ) -> None:
        """Initialize a new Python package project.

        :param name: This is the name of your project. Default: $BASEDIR
        
        :param import_module_name: Name of the python package as used in imports and filenames. \
            Must only consist of alphabetic characters and underscores. \
            Defaults to project name with hyphens replaced by underscores.
        
        :param outdir: The root directory of the project. Relative to this directory, all files are synthesized. \
            If this project has a parent, this directory is relative to the parent directory and it cannot be the \
            same as the parent or any of it's other sub-projects. Default: "."
        
        :param parent: The parent project, if this project is part of a bigger project.
        """
        super().__init__(repo)

        # validate inputs
        assert__project_name__is_valid(name)
        assert__domain__is_valid(domain)
        if import_module_name:
            assert__import_module_name__is_valid(import_module_name)

        # store inputs as attrs
        self.outdir = Path("domains") / domain / (outdir or name)
        self.domain = domain
        self.repo: "Repository" = repo
        self.name = name
        self.import_module_name = name.replace("-", "_") if not import_module_name else import_module_name
        self.src_dir = self.outdir / "src"
        self.package_dir = self.src_dir / self.import_module_name

        # register self as project on the parent directory
        repo.metaflow_projects.append(self)
        self.flows: list[MetaflowFlow] = []

        ################################
        # --- Add child components --- #
        ################################

        self.init_py = LazySampleFile(
            self.repo,
            file_path=(self.package_dir / "__init__.py").resolve(),
            get_contents_fn=lambda: f'"""Module for {self.name}"""\n',
        )

        self.pyproject_toml = PyprojectToml(
            project=self.repo,
            file_path=self.outdir / "pyproject.toml",
            description=get_package_description(domain=domain),
            package_name=self.name,
        )

        self.readme = Readme(
            project=self.repo,
            package_name=self.name,
            file_path=self.outdir / "README.md",
        )

    def add_flow(  # noqa: PLR0913 -- Too many arguments in function definition
        self,
        filename: str,
    ) -> MetaflowFlow:
        """Add a new flow to the project.

        :param filename: E.g. "backtest_flow.py".
        """
        return MetaflowFlow(
            scope=self,
            filename=filename,
        )

    def pre_synthesize(self) -> None:
        """Run validations before synthesizing the files."""
        if len(self.flows) == 0:
            err_msg = dedent(f"""\n\n
            ==========================

            💡 No flows found in the project MetaflowProject(name="{self.name}") in `.projenrc.py`.

            You likely set up the MetaflowProject() correctly. 
            
            But it does not make sense to have a MetaflowProject with out at least one flow.

            Register a flow with `my_metaflow_project.add_flow(filename="my_flow.py")`.
            """)
            raise ValueError(err_msg)

        """Add final components before synthesizing the files.

        The github actions workflow must be created after all the flows are added.

        I.e. after `some_project.add_flow(filename="some_flow.py")` has been called.

        So it cannot be called in the __init__() method because the flows have not
        been added yet.
        """
        self.ci_cd_workflow = MetaflowProjectCiCdGitHubActionsWorkflow(metaflow_project=self)


def get_package_description(domain: TDataScienceDomain) -> str:
    """Return `A metaflow flow. For questions, reach out to <lead 1>, ..., or <lead N>.`."""
    assert__domain__is_valid(domain)
    domain_leads = DATA_SCIENCE_DOMAINS[domain]
    if len(domain_leads) > 1:
        leads = ", ".join(domain_leads[:-1]) + f", or {domain_leads[-1]}"
    else:
        leads = domain_leads[0]
    return f"A metaflow flow. For questions, reach out to {leads}."


def assert__domain__is_valid(domain: str) -> None:
    """Validate the domain string and convert it to a Domain enum."""
    if domain not in DATA_SCIENCE_DOMAINS.keys():
        raise ValueError(f"Invalid domain: {domain}. Must be one of {', '.join(DATA_SCIENCE_DOMAINS.keys())}")


def assert__project_name__is_valid(name: str):
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
        err_msg = "Project name must:\n- Only contain lowercase letters and hyphens\n- Start and end with a letter"
        raise ValueError(err_msg)


def assert__import_module_name__is_valid(name: str) -> str:
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
