from typing import TYPE_CHECKING

from projen import Project

if TYPE_CHECKING:
    from ds_projen.projects.ds_project.project import MetaflowProject


class Repository(Project):
    """Parent node for all projen components.

    Every projen project should have at least one `Repository`
    that other components such as `MetaflowProject`s can be added to.
    """

    def __init__(self, name: str, outdir: str | None = None, parent: Project | None = None) -> None:
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
