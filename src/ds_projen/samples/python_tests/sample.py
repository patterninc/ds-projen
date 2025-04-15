"""A set of sample folders and files that demonstrate a successful pytest framework."""

from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from projen import Component, Project, SampleFile

if TYPE_CHECKING:
    pass

THIS_DIR = Path(__file__).parent
TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR = (THIS_DIR / "./templates/tests").resolve().absolute()


class SamplePythonTestingFramework(Component):
    """A set of sample folders and files that demonstrate a successful pytest framework."""

    def __init__(
        self,
        project: Project,
        tests_outdir: Union[Path, str],
    ) -> None:
        super().__init__(scope=project)
        self.fastapi_sample_files = self.__make_sample_dir(tests_outdir=tests_outdir)

    def __make_sample_dir(self, tests_outdir: Union[Path, str]) -> List[SampleFile]:
        template_fpaths = self.__get_sample_file_template_fpaths()
        return [
            SampleFile(
                project=self.project,
                file_path=str(tests_outdir / path.relative_to(TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR)),
                contents=path.read_text(),
            )
            for path in template_fpaths
        ]

    def __get_sample_file_template_fpaths(self) -> List[Path]:
        template_fpaths = list(TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR.rglob("*.py"))
        return template_fpaths
