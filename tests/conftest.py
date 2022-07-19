import os
from pathlib import Path


def pytest_configure():
    # set env var for data path to sample test data location
    os.environ["SPINEQ_HOME"] = str(Path(__file__).parent / "sample")
