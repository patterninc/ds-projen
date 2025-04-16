"""A set of sample folders and files that demonstrate a successful pytest framework."""

from pathlib import Path
from typing import TYPE_CHECKING

from projen import Component, Project, SampleFile

if TYPE_CHECKING:
    pass

THIS_DIR = Path(__file__).parent
TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR = (THIS_DIR / "./templates").resolve().absolute()


class SamplePythonTestingFramework(Component):
    """A set of sample folders and files that demonstrate a successful pytest framework."""

    def __init__(
        self,
        scope: Project,
        tests_outdir: Path | str,
    ) -> None:
        super().__init__(scope)
        print(f"{tests_outdir=}")
        print(f"{self.project.outdir=}")
        print(f"{TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR=}")

        self.fastapi_sample_files = self.__make_sample_dir(tests_outdir=tests_outdir)

    def __make_sample_dir(self, tests_outdir: Path | str) -> list[SampleFile]:
        template_fpaths = self.__get_sample_file_template_fpaths()

        sample_files = []
        for path in template_fpaths:
            fpath = str(Path(tests_outdir) / path.relative_to(TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR))
            print(f"Sample file path: {fpath=}")
            print(f"{path.relative_to(TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR)=}")
            SampleFile(
                project=self.project,
                file_path=fpath,
                contents=path.read_text(),
            )

        return sample_files

    def __get_sample_file_template_fpaths(self) -> list[Path]:
        template_fpaths = list(TESTING_FRAMEWORK_SAMPLE_FILE_TEMPLATES_DIR.rglob("*.py"))
        return template_fpaths
