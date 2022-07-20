import numpy as np
from shapely.geometry import Point

from spineq import mappings


def test_point_to_oa():
    assert mappings.point_to_oa(Point(425800, 568100)) == "E00042201"
    assert np.isnan(mappings.point_to_oa(Point(415800, 558100)))


def test_oa_to_la():
    assert mappings.oa_to_la("E00042480") == "E08000021"


def test_la_to_oas():
    oas = sorted(mappings.la_to_oas("E08000037"))
    assert oas == sorted(
        [
            "E00041645",
            "E00041587",
            "E00041395",
            "E00041404",
            "E00041435",
            "E00041445",
            "E00041617",
            "E00041954",
            "E00041978",
            "E00041924",
            "E00166205",
        ]
    )


def test_la_to_lsoas():
    lsoas = sorted(mappings.la_to_lsoas("E08000021"))
    assert lsoas == sorted(
        [
            "E01008376",
            "E01008322",
            "E01008355",
            "E01008359",
            "E01008321",
            "E01008438",
            "E01033554",
            "E01033543",
            "E01008387",
            "E01008402",
            "E01008419",
            "E01008395",
            "E01033545",
            "E01008437",
        ]
    )


def test_lsoa_to_oas():
    oas = sorted(mappings.lsoa_to_oas("E01008355"))
    assert oas == ["E00042370", "E00042378"]


def test_lad20cd_to_lad11cd():
    assert mappings.lad20cd_to_lad11cd("E08000037") == "E08000020"


def test_lad11cd_to_lad20cd():
    assert mappings.lad11cd_to_lad20cd("E08000020") == "E08000037"


def test_lad20nm_to_lad20cd():
    assert mappings.lad20nm_to_lad20cd("Newcastle upon Tyne") == "E08000021"


def test_lad20cd_to_lad20nm():
    assert mappings.lad20cd_to_lad20nm("E08000021") == "Newcastle upon Tyne"


def test_lad11nm_to_lad11cd():
    assert mappings.lad11nm_to_lad11cd("Gateshead") == "E08000020"
