import os
from pathlib import Path

import pytest


def pytest_configure():
    # set env var for data path to sample test data location
    os.environ["SPINEQ_HOME"] = str(Path(__file__).parent / "sample")


@pytest.fixture
def sample_params():
    return {
        "total": {"n_oa": 27, "n_lsoa": 25, "n_school": 29, "n_urb_obs": 10},
        "newcastle": {"lad20cd": "E08000021", "n_oa": 16, "n_lsoa": 14},
        "gateshead": {
            "lad20cd": "E08000037",
            "n_oa": 11,
            "n_lsoa": 11,
            "n_school": 12,
            "lad20nm": "Gateshead",
        },
    }
