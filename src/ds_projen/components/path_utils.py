"""Utilities for locating standard projen paths."""

import sys
from pathlib import Path

from projen import Project


def get_project_dir_name(project: Project) -> str:
    """Return the folder name containing the the project that is being generated."""
    return get_project_dir(project).name


def get_project_dir(project: Project) -> Path:
    """Return the folder name containing the the project that is being generated."""
    if project.parent:
        package_outdir = project.outdir
        return Path(package_outdir)

    # if outdir is not provided, it means this projen project is not a mono-repo,
    # so we assume that the python package is in the root of the repository,
    # so the package directory name, should be the name of the repository folder
    return get_projenrc_path()


def get_projenrc_path() -> Path:
    """Return the path to the projenrc.py file currently being executed."""
    return Path(sys.path[0])


def get_projenrc_folder() -> Path:
    """Return the folder containing the projenrc.py file currently being executed."""
    return get_projenrc_path().parent
