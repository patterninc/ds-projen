"""A Flow that can be added to a MetaflowProject."""

from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING

from projen import Component

from ds_projen.components.lazy_sample_file import LazySampleFile

if TYPE_CHECKING:
    from ds_projen.components.metaflow_project.metaflow_project import MetaflowProject


class MetaflowFlow(Component):
    """A Flow that can be added to a MetaflowProject."""

    def __init__(
        self,
        scope: "MetaflowProject",
        filename: str,
    ) -> None:
        super().__init__(scope)

        assert_flow_filename_is_valid(filename=filename)

        scope.flows.append(self)  # register self to the parent project
        self.flow_path = scope.src_dir / filename  # create self in the parent's src/ dir
        self.flow_name = get_flow_class_name_from_filepath(flow_path=self.flow_path)

        def get_flow_template():
            return self._get_flow_template(flow_name=self.flow_name)

        self._flow_file = LazySampleFile(
            project=scope.project,
            file_path=self.flow_path,
            get_contents_fn=get_flow_template,
        )

    def _get_flow_template(
        self,
        flow_name: str,
    ) -> str:
        flow_template = dedent(f'''\
            """A Metaflow flow."""

            from metaflow import FlowSpec, step, pypi_base

            @pypi_base(
                python="3.11",
                packages={{"requests": "2.32.3"}}
            )
            class {flow_name}(FlowSpec):
                """A sample flow."""

                @step
                def start(self):
                    """Start the flow."""
                    self.next(self.end)

                @step
                def end(self):
                    """End the flow."""
                    pass

            if __name__ == "__main__":
                {flow_name}()
            ''')

        return flow_template


def assert_flow_filename_is_valid(filename: str):
    """Assert that the flow name is valid.

    A valid flow name must be a valid Python identifier.
    """
    if not filename.endswith("_flow.py"):
        raise ValueError(f"Invalid flow filename: {filename}. Flow filenames must end with '_flow.py'.")

    flow_name = filename[:-3]
    if not flow_name.isidentifier():
        raise ValueError(
            f"Invalid flow name: {filename}. Flow names must be valid Python identifiers. E.g. lower_snake_case_flow.py"
        )

    if not flow_name.islower():
        raise ValueError(
            f"Invalid flow name: {filename}. Flow names must be lower snake case. E.g. lower_snake_case_flow.py"
        )


def get_flow_class_name_from_filepath(flow_path: str | Path) -> str:
    """Derive the flow class name from the flow file path.

    E.g. `path/to/some_backtest_flow.py` -> `SomeBacktest`
    """
    flow_path = Path(flow_path)  # ex: "path/to/some_backtest_flow.py"
    filename_no_ext = flow_path.stem  # ex: "some_backtest_flow"

    # ex: SomeBacktest
    flow_name = "".join(s.title() for s in filename_no_ext.replace("-", "_").split("_"))

    return flow_name
