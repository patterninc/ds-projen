import shutil
from typing import Generator

import pytest

from tests.consts import ARTIFACTS_DIR


# fixture scope is set to "module" assuming each test module(test file) will use a single artifacts directory
@pytest.fixture(scope="module", autouse=True, name="test_artifacts_dir")
def test_artifacts_dir() -> Generator[None, None, None]:
    """Create an artifacts directory for test files and remove it after the tests.

    With `autouse=False`:
    - Tests must explicitly declare dependency on test_artifacts_dir
    - This makes it easier to track tests that are dependentent of this fixture.
    - Makes it clear which tests need temporary file storage.
    - Example usage in a test:
        ```
        @pytest.fixture
        def repository_fpath(test_artifacts_dir):
            with tempfile.TemporaryDirectory(dir=test_artifacts_dir) as tmp_dir:
                tmp_dir = Path(tmp_dir)
        ```

    With `autouse=True` (current):
    - Fixture runs automatically for all tests in all modules
    - This makes it harder to track which tests are dependent on this fixture.
    - Good for truly global setup
    - In future, if we want to use this fixture in all tests, we can set autouse=True
    - Example usage in a test fixture:
        ```
        from tests.consts import ARTIFACTS_DIR
        @pytest.fixture
        def repository_fpath():
            with tempfile.TemporaryDirectory(dir=ARTIFACTS_DIR) as tmp_dir:
                tmp_dir = Path(tmp_dir)
        ```
    """
    ARTIFACTS_DIR.mkdir(exist_ok=True, parents=True)
    yield  # this will run the tests
    shutil.rmtree(ARTIFACTS_DIR, ignore_errors=True)
