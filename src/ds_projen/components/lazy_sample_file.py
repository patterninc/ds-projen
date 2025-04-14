"""Define a way to specify non-tamper proof files, whose contents are derived lazily."""

from pathlib import Path
from typing import Callable, Optional, Union

from projen import Component, Project

TGetContentsFn = Callable[[], str]
"""A function that will be called during synthesis of a component to get the contents that will be written to the file."""

TGetFilePathFn = Callable[[], Union[str, Path]]


class LazySampleFile(Component):
    """A file that is not tamper-proof.

    This class differs from ``projen.SampleFile`` in that the contents are derived "lazily".
    This is to say, the actual contents of a ``LazySampleFile`` are not decided until
    ``synthesize()`` is called. ``synthesize()`` will execute the provided
    ``get_contents_fn()`` to decide the contents.

    See ``TemplatizedSampleFile`` for an example of why the ability to defer
    the deciding of file contents is useful.

    Sample files are typically meant to

    1. save developers from writing boilerplate
    2. suggest a certain set of practices; for example, you might use sample files
       to structure a FastAPI application in a particular way

    Since sample files are not tamper-proof, they have these two properties:

    1. developers can completely disregard any suggestions within
    2. updates to a library of sample files made by a platform team will not
       automatically propagate to projects that were initialized with an
       older set of sample files; in this case, developers can regenerate
       a newer set of sample files and manually bring any desired changes
       into their existing project if they want certain updates
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project: "Project",
        file_path: str | Path | None = None,
        get_file_path_fn: TGetFilePathFn | None = None,
        get_contents_fn: TGetContentsFn | None = None,
        file_encoding: str | None = None,
    ):
        super().__init__(project)

        assert not (file_path and get_file_path_fn), "file_path and get_file_path_fn cannot both be set"
        assert file_path or get_file_path_fn, "one of file_path or get_file_path_fn must be set"

        self.file_encoding = file_encoding
        self.get_contents_fn = get_contents_fn
        self.file_path: str | Path = file_path
        """File path relative to ``project.outdir`` where the final sample file will be created."""
        self.get_file_path_fn: TGetFilePathFn = get_file_path_fn or (lambda: self.file_path)

    def synthesize(self) -> None:
        """Write the file contents to disk if file is not already present."""
        contents: str = self.get_contents_fn()
        file_path = self.get_file_path_fn()
        final_fpath = Path(self.project.outdir) / Path(file_path)
        write_file_if_not_exists(contents=contents, path=final_fpath, encoding=self.file_encoding)


def write_file_if_not_exists(path: Path, contents: str, encoding: Optional[str] = None):
    """Write the file contents to disk if file is not already present."""
    if not path.exists():
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_text(data=contents, encoding=encoding)
