import geopandas as gpd
import numpy as np
import pandas as pd
import pytest

from spineq.data.census import CentroidDataset, OABoundaryDataset, PopulationDataset


@pytest.fixture
def lad20cd():
    return "E08000021"  # Newcastle upon tyne


@pytest.fixture
def n_oa_total():
    return 27  # number of OA in sample data


@pytest.fixture
def n_oa_la():
    return 16  # number of OA in Newcastle in sample data


class TestConfig:
    def __init__(self, lad20cd, n_oa_total, n_oa_la):
        self.lad20cd = lad20cd
        self.n_oa_total = n_oa_total
        self.n_oa_la = n_oa_la


class TestCentroidDataset(TestConfig):
    def test_init_defaults(self):
        dataset = CentroidDataset()
        assert isinstance(dataset, CentroidDataset)
        assert dataset.name == "centroids"
        assert dataset.title == "Output Area Centroids"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == self.n_oa_total
        np.testing.assert_array_equal(dataset.values.columns, ["x", "y", "geometry"])

    def test_init_all(self):
        dataset = CentroidDataset(
            lad20cd=self.lad20cd, name="NAME", title="TITLE", description="DESCRIPTION"
        )
        assert isinstance(dataset, CentroidDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == self.n_oa_la
        np.testing.assert_array_equal(dataset.values.columns, ["x", "y", "geometry"])


class TestOABoundaryDataset(TestConfig):
    def test_init_defaults(self):
        dataset = OABoundaryDataset()
        assert isinstance(dataset, OABoundaryDataset)
        assert dataset.name == "oa_boundary"
        assert dataset.title == "Output Area Boundaries"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == self.n_oa_total
        np.testing.assert_array_equal(dataset.values.columns, ["geometry"])

    def test_init_all(self):
        dataset = OABoundaryDataset(
            lad20cd=self.lad20cd, name="NAME", title="TITLE", description="DESCRIPTION"
        )
        assert isinstance(dataset, OABoundaryDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == self.n_oa_la
        np.testing.assert_array_equal(dataset.values.columns, ["geometry"])


class TestPopulationDataset(TestConfig):
    @pytest.fixture
    def dataset():
        return PopulationDataset()

    def test_init_defaults(self, dataset):
        assert isinstance(dataset, PopulationDataset)
        assert dataset.name == "population"
        assert dataset.title == "Number of Residents"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == self.n_oa_total
        np.testing.assert_array_equal(dataset.values.columns, range(91))

    def test_init_all(self):
        dataset = PopulationDataset(
            lad20cd=self.lad20cd, name="NAME", title="TITLE", description="DESCRIPTION"
        )
        assert isinstance(dataset, PopulationDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == self.n_oa_la
        np.testing.assert_array_equal(dataset.values.columns, range(91))

    def test_filter_age_defaults(self, dataset):
        # if no age range given, no rows removed
        filt_pop = dataset.filter_age()
        pd.testing.assert_frame_equal(dataset.values, filt_pop.values)
        assert filt_pop.name == "population_0_to_90"
        assert filt_pop.title == "Residents Between 0 and 90 Years Old"

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
        ...


class TestWorkplaceDataset:
    def test_init(self):
        ...


class TestHealthDataset:
    def test_init(self):
        ...
