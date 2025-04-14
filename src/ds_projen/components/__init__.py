"""Module for classes that inherit from `projen.Component`."""

# silence JSII warnings; the risk of accidentally doing something bad
# due to having a version of node installed that hasn't been tested with projen is
# *extremely* low. Even if something happened, all this is doing is rewriting text files.
import os

os.environ["JSII_SILENCE_WARNING_UNTESTED_NODE_VERSION"] = "1"
