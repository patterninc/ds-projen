from pathlib import Path

from projen import Component, Project

from ds_projen.components.lazy_sample_file import LazySampleFile


class Flow(Component):
    """A Metaflow flow Component."""

    def __init__(
        self,
        project: "Project",
        flow_name: str,
        flow_path: str | Path,
        use_pypi_base: bool | None = True,
        use_conda_base: bool | None = None,
        python_version: str | None = "3.11",
        packages: dict[str, str] = {},  # noqa: B006 -- Do not use mutable data structures for argument defaults
    ) -> None:
        super().__init__(project)
        self.flow_name = flow_name.capitalize()
        self.flow_path = Path(flow_path)

        self._flow_file = LazySampleFile(
            project=project,
            file_path=self.flow_path,
            get_contents_fn=lambda: self._get_flow_template(
                flow_name=self.flow_name,
                use_pypi_base=use_pypi_base,
                use_conda_base=use_conda_base,
                python_version=python_version,
                packages=packages,
                config_path=None,
            ),
        )

    def _get_flow_template(  # noqa: PLR0913 -- Too many arguments in function definition
        self,
        flow_name: str,
        use_pypi_base: bool | None,
        use_conda_base: bool | None,
        python_version: str | None,
        packages: dict[str, str],
        config_path: str | Path | None,
    ) -> str:
        """Get the flow template."""
        package_manager = "pypi_base"
        if use_conda_base:
            package_manager = "conda_base"

        flow_template = f'''"""A Metaflow flow."""\n
from metaflow import FlowSpec, step, {package_manager}

@{package_manager}(
    python_version="{python_version}",
    packages={packages}
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
'''

        return flow_template
