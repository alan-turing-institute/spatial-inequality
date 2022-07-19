import os

import spineq.config
from spineq import mappings


def test_point_to_oa():

    assert (
        os.environ["SPINEQ_HOME"]
        == "/Users/jroberts/GitHub/spatial-inequality/tests/sample"
    )
    assert (
        str(spineq.config.DATA_DIR)
        == "/Users/jroberts/GitHub/spatial-inequality/tests/sample/data"
    )


def test_oa_to_la():
    ...


def test_la_to_oas():
    ...


def test_la_to_lsoas():
    ...


def test_lsoa_to_oas():
    ...


def test_lad20cd_to_lad11cd():

    assert mappings.lad20cd_to_lad20nm("E08000021") == "Newcastle upon Tyne"


def test_lad11cd_to_lad20cd():
    ...


def test_lad20nm_to_lad20cd():
    from spineq import mappings

    assert mappings.lad20nm_to_lad20cd("Newcastle upon Tyne") == "E08000021"


def test_lad20cd_to_lad20nm():
    ...


def test_lad11nm_to_lad11cd():
    ...
