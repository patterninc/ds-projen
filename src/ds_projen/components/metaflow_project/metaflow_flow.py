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

        scope.flows.append(self)  # register self to the parent project
        self.flow_path = scope.src_dir / filename  # create self in the parent's src/ dir

        def get_flow_template():
            flow_name = get_flow_class_name_from_filepath(flow_path=self.flow_path)
            return self._get_flow_template(flow_name=flow_name)

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
                packages={{"pandas": "2.2.3"}}
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


def get_flow_class_name_from_filepath(flow_path: str | Path) -> str:
    """Derive the flow class name from the flow file path.

    E.g. `path/to/some_backtest_flow.py` -> `SomeBacktest`
    """
    flow_path = Path(flow_path)  # ex: "path/to/some_backtest_flow.py"
    filename_no_ext = flow_path.stem  # ex: "some_backtest_flow"
    file_name_with__flow_py__stripped = filename_no_ext.replace("flow", "").strip("_")  # ex: some_backtest

    # ex: SomeBacktest
    flow_name = "".join(s.title() for s in file_name_with__flow_py__stripped.replace("-", "_").split("_"))

    return flow_name
