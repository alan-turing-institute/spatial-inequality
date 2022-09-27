import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from spineq.data.census import (
    CentroidDataset,
    HealthDataset,
    OABoundaryDataset,
    PopulationDataset,
    WorkplaceDataset,
)

test_la_key = "newcastle"


class TestCentroidDataset:
    def test_init_defaults(self, sample_params):
        dataset = CentroidDataset()
        assert isinstance(dataset, CentroidDataset)
        assert dataset.name == "centroids"
        assert dataset.title == "Output Area Centroids"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params["total"]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["x", "y", "geometry"])

    def test_init_all(self, sample_params):
        dataset = CentroidDataset(
            lad20cd=sample_params[test_la_key]["lad20cd"],
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, CentroidDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["x", "y", "geometry"])


class TestOABoundaryDataset:
    def test_init_defaults(self, sample_params):
        dataset = OABoundaryDataset()
        assert isinstance(dataset, OABoundaryDataset)
        assert dataset.name == "oa_boundary"
        assert dataset.title == "Output Area Boundaries"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params["total"]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["geometry"])

    def test_init_all(self, sample_params):
        dataset = OABoundaryDataset(
            lad20cd=sample_params[test_la_key]["lad20cd"],
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, OABoundaryDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["geometry"])


class TestPopulationDataset:
    @pytest.fixture
    def dataset(self):
        return PopulationDataset()

    def test_init_defaults(self, dataset, sample_params):
        assert isinstance(dataset, PopulationDataset)
        assert dataset.name == "population"
        assert dataset.title == "Number of Residents"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params["total"]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, range(91))

    def test_init_all(self, sample_params):
        dataset = PopulationDataset(
            lad20cd=sample_params[test_la_key]["lad20cd"],
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, PopulationDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, range(91))

    def test_filter_age_defaults(self, dataset):
        # if no age range given, no rows removed
        filt_pop = dataset.filter_age()
        pd.testing.assert_frame_equal(dataset.values, filt_pop.values)
        assert filt_pop.name == "population_0_to_90"
        assert filt_pop.title == "Number of Residents Between 0 and 90 Years Old"

    def test_filter_age_labels(self, dataset):
        filt_pop = dataset.filter_age(
            name="NAME", title="TITLE", description="DESCRIPTION"
        )
        assert filt_pop.name == "NAME"
        assert filt_pop.title == "TITLE"
        assert filt_pop.description == "DESCRIPTION"

    def test_filter_age_range(self, dataset):
        filt_pop = dataset.filter_age(low=10, high=20)
        np.testing.assert_array_equal(filt_pop.values.columns, range(10, 21))

    def test_to_total(self, dataset):
        total = dataset.to_total()
        assert isinstance(total, PopulationDataset)
        exp_totals = pd.Series(
            {
                "E00041395": 808,
                "E00041404": 316,
                "E00041435": 351,
                "E00041445": 273,
                "E00041587": 283,
                "E00041617": 325,
                "E00041645": 445,
                "E00041924": 282,
                "E00041954": 256,
                "E00041978": 309,
                "E00042201": 290,
                "E00042219": 323,
                "E00042370": 275,
                "E00042378": 371,
                "E00042433": 246,
                "E00042480": 294,
                "E00042538": 285,
                "E00042609": 984,
                "E00042610": 287,
                "E00042625": 277,
                "E00042735": 223,
                "E00042807": 240,
                "E00042825": 730,
                "E00042826": 652,
                "E00166205": 185,
                "E00175559": 820,
                "E00175577": 385,
            },
            name="total",
        )
        exp_totals.index.name = "oa11cd"
        pd.testing.assert_series_equal(total.values["total"].sort_index(), exp_totals)


class TestWorkplaceDataset:
    def test_init_defaults(self, sample_params):
        dataset = WorkplaceDataset()
        assert isinstance(dataset, WorkplaceDataset)
        assert dataset.name == "workplace"
        assert dataset.title == "Number of Workers"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params["total"]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["workers"])

    def test_init_all(self, sample_params):
        dataset = WorkplaceDataset(
            lad20cd=sample_params[test_la_key]["lad20cd"],
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, WorkplaceDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(dataset.values.columns, ["workers"])


class TestHealthDataset:
    def test_init_defaults(self, sample_params):
        dataset = HealthDataset()
        assert isinstance(dataset, HealthDataset)
        assert dataset.name == "health"
        assert dataset.title == "Long-term Health Issues and Disabilty"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params["total"]["n_lsoa"]
        np.testing.assert_array_equal(dataset.values.columns, ["health_or_disability"])

    def test_init_all(self, sample_params):
        dataset = HealthDataset(
            lad20cd=sample_params[test_la_key]["lad20cd"],
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, HealthDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params[test_la_key]["n_lsoa"]
        np.testing.assert_array_equal(dataset.values.columns, ["health_or_disability"])
