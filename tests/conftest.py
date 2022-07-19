import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    os.environ["SPINEQ_HOME"] = str(Path(__file__).parent / "sample")
