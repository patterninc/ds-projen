"""Sample test to showcase how to author tests."""

from tests.consts import ARTIFACTS_DIR


def test__sample_test():
    assert ARTIFACTS_DIR.name == "artifacts"
