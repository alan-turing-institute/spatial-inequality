from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from spineq.data.base import Dataset, LSOADataset, OADataset, PointDataset
from spineq.data.local_authority import LocalAuthority

test_la_key = "gateshead"


@pytest.fixture
def la(sample_params):
    return LocalAuthority(sample_params[test_la_key]["lad20cd"])


class TestDataset:
    @pytest.fixture
    def values(self):
        return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    @pytest.fixture
    def dataset(self, values):
        return Dataset("NAME", values)

    def test_init_defaults(self, values):
        d = Dataset("NAME", values)
        assert isinstance(d, Dataset)
        assert d.name == "NAME"
        pd.testing.assert_frame_equal(d.values, values)
        assert d.title == ""
        assert d.description == ""

    def test_init_all(self, values):
        d = Dataset("NAME", values, index="a", title="TITLE", description="DESCRIPTION")
        assert isinstance(d, Dataset)
        assert d.title == "TITLE"
        assert d.description == "DESCRIPTION"
        pd.testing.assert_frame_equal(d.values, values.set_index("a"))

    def test_len(self, dataset):
        assert len(dataset) == 3

    def test_repr(self, dataset):
        assert repr(dataset) == "Dataset: NAME (3 rows)"

    def test_get(self, values, dataset):
        np.testing.assert_array_equal(dataset["a"], values["a"])

    def test_read_pandas(self, sample_params):
        path = Path(__file__).parent / "../../sample/data/raw/centroids.csv"
        d = Dataset.read_pandas("NAME", path)
        assert isinstance(d, Dataset)
        assert isinstance(d.values, pd.DataFrame)
        assert len(d) == sample_params["total"]["n_oa"]

    def test_read_geopandas(self, sample_params):
        path = Path(__file__).parent / "../../sample/data/raw/oa_shape"
        d = Dataset.read_geopandas("NAME", path)
        assert isinstance(d, Dataset)
        assert isinstance(d.values, gpd.GeoDataFrame)
        assert len(d) == sample_params["total"]["n_oa"]

    def test_to_oa_dataset(self, dataset):
        with pytest.raises(NotImplementedError):
            dataset.to_oa_dataset()

    def test_filter_la(self, dataset):
        with pytest.raises(NotImplementedError):
            dataset.filter_la()


class TestPointDataset:
    @pytest.fixture
    def values(self):
        path = Path(__file__).parent / "../../sample/data/raw/schools.csv"
        values = gpd.GeoDataFrame(pd.read_csv(path))
        values["geometry"] = gpd.points_from_xy(
            values["Easting"], values["Northing"], crs="EPSG:27700"
        )
        return values[["NumberOfPupils", "geometry"]]

    @pytest.fixture
    def dataset(self, values):
        return PointDataset("NAME", values)

    def test_init(self, dataset):
        assert isinstance(dataset, PointDataset)

    def test_to_oa_dataset(self, dataset):
        oa_d = dataset.to_oa_dataset()
        assert isinstance(oa_d, OADataset)
        exp_counts = pd.Series(
            {
                "E00041395": 407.0,
                "E00041404": 60.0,
                "E00041435": 1439.0,
                "E00041445": 0.0,
                "E00041617": 1317.0,
                "E00041645": 0.0,
                "E00041924": 432.0,
                "E00041954": 206.0,
                "E00041978": 244.0,
                "E00042201": 1446.0,
                "E00042219": 419.0,
                "E00042433": 240.0,
                "E00042480": 197.0,
                "E00042538": 0.0,
                "E00042610": 453.0,
                "E00042625": 1846.0,
                "E00042807": 0.0,
                "E00042825": 237.0,
                "E00175559": 197.0,
                "E00175577": 239.0,
            },
            name="NumberOfPupils",
        )
        exp_counts.index.name = "oa11cd"
        pd.testing.assert_series_equal(oa_d["NumberOfPupils"].sort_index(), exp_counts)

    def test_filter_la(self, dataset, la, sample_params):
        filt_points = dataset.filter_la(la)
        assert isinstance(filt_points, PointDataset)
        assert len(filt_points) == sample_params[test_la_key]["n_school"]


class TestOADataset:
    @pytest.fixture
    def values(self):
        path = Path(__file__).parent / "../../sample/data/raw/centroids.csv"
        return pd.read_csv(path)

    @pytest.fixture
    def dataset(self, values):
        return OADataset("NAME", values)

    def test_init(self, values, dataset):
        assert isinstance(dataset, OADataset)
        pd.testing.assert_frame_equal(dataset.values, values.set_index("oa11cd"))

    def test_to_oa_dataset(self, dataset):
        oa_d = dataset.to_oa_dataset()
        assert isinstance(oa_d, OADataset)
        pd.testing.assert_frame_equal(dataset.values, oa_d.values)

    def test_filter_la(self, dataset, la, sample_params):
        filt_oa = dataset.filter_la(la)
        assert isinstance(filt_oa, OADataset)
        assert len(filt_oa) == sample_params[test_la_key]["n_oa"]


class TestLSOADataset:
    @pytest.fixture
    def values(self):
        path = Path(__file__).parent / "../../sample/data/raw/health.csv"
        return pd.read_csv(path)

    @pytest.fixture
    def dataset(self, values):
        return LSOADataset("NAME", values)

    def test_init(self, values, dataset):
        assert isinstance(dataset, LSOADataset)
        pd.testing.assert_frame_equal(dataset.values, values.set_index("lsoa11cd"))

    def test_to_oa_dataset_no_weights(self, dataset):
        oa_d = dataset.to_oa_dataset()
        assert isinstance(oa_d, OADataset)
        # lsoa with only one oa
        assert oa_d["health_or_disability"].loc["E00042219"] == 1528
        # lsoa with two oas, split lsoa equally
        assert oa_d["health_or_disability"].loc["E00042370"] == 772
        assert oa_d["health_or_disability"].loc["E00042378"] == 772

    def test_to_oa_dataset_with_weights(self, dataset):
        path = Path(__file__).parent / "../../sample/data/raw/population_total.csv"
        weights = pd.read_csv(path).set_index("oa11cd")["population"]
        oa_d = dataset.to_oa_dataset(oa_weights=weights)
        assert isinstance(oa_d, OADataset)
        # lsoa with only one oa (result should be same as unweighted)
        assert oa_d["health_or_disability"].loc["E00042219"] == 1528
        # lsoa with two oas, split weighted by OA population
        assert oa_d["health_or_disability"].loc["E00042370"] == pytest.approx(657.276)
        assert oa_d["health_or_disability"].loc["E00042378"] == pytest.approx(886.724)

    def test_filter_la(self, dataset, la, sample_params):
        filt_lsoa = dataset.filter_la(la)
        assert isinstance(filt_lsoa, LSOADataset)
        assert len(filt_lsoa) == sample_params[test_la_key]["n_lsoa"]
