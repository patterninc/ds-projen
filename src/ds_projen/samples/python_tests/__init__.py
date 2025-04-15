"""Sample Python Testing Framework.

All the files in ./templates/ are not meant to be imported as part of this package.
They are actually template files that will be rendered into wherever the sample.py:Component
is used.
"""

from .sample import SamplePythonTestingFramework

__all__ = ["SamplePythonTestingFramework"]
