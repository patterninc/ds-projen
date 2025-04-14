from pathlib import Path
from typing import TYPE_CHECKING

from projen import Project

from ds_projen.components.path_utils import get_project_dir
from ds_projen.projects.repository.gitignore import DEFAULT_GITIGNORE_PATTERNS

if TYPE_CHECKING:
    from ds_projen.projects.ds_project.project import MetaflowProject


class Repository(Project):
    """Parent node for all projen components.

    Every projen project should have at least one `Repository`
    that other components such as `MetaflowProject`s can be added to.
    """

    def __init__(
        self,
        name: str,
        outdir: str | None = None,
        parent: Project | None = None,
    ) -> None:
        """Initialize a mono-repo project.

        Use this project as a collection for other projects.

        :param name: This is the name of your project. Default: $BASEDIR
        :param outdir: The root directory of the project. Relative to this directory, all files are
                       synthesized. If this project has a parent, this directory is relative to the
                       parent directory and it cannot be the same as the parent or any of it's other
                       sub-projects. Default: "."
        :param parent: The parent project, if this project is part of a bigger project.
        """
        super().__init__(
            name=name,
            outdir=name if parent and not outdir else outdir,
            parent=parent,
            commit_generated=True,
            logging=None,
            projen_command=None,
            projenrc_json=None,
            projenrc_json_options=None,
            renovatebot=None,
            renovatebot_options=None,
        )
        self.metaflow_projects: list["MetaflowProject"] = []
        
        # TODO: Add a pyproject.toml file at the root of the repo
        # TODO: Add a README.md file at the root of the repo
        # TODO: Add a pre-commit config file at the root level of the repo
        # TODO: Add a `run` task runner
        # TODO: .vscode directory
        # TODO: Managing github worklfows for the projects
        
        # Add gitignore
        self.gitignore.add_patterns(*DEFAULT_GITIGNORE_PATTERNS)

    def post_synthesize(self) -> None:
        """React to the project being synthesized."""
        _sort_gitignore_in_place(project=self)
        return super().post_synthesize()


def _sort_gitignore_in_place(project: Project):
    repo_root_dir: Path = get_project_dir(project=project)
    gitignore_fpath = repo_root_dir / ".gitignore"

    # read the sorts lines
    gitignore_lines = gitignore_fpath.read_text().splitlines()

    # sort the lines
    marker: str = gitignore_lines[0]
    ignores: list[str] = gitignore_lines[1:]

    # remove read only gitignore file
    gitignore_fpath.unlink()

    # write the lines to disk as a read only file
    new_gitignore_lines = [marker] + sorted(ignores)
    gitignore_fpath.write_text("\n".join(new_gitignore_lines))

    # make gitignore read only
    gitignore_fpath.chmod(0o444)
