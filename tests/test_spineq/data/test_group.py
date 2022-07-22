from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from spineq.data.base import OADataset
from spineq.data.census import (
    CentroidDataset,
    HealthDataset,
    OABoundaryDataset,
    PopulationDataset,
)
from spineq.data.group import DatasetGroup, LocalAuthority
from spineq.data.school import SchoolDataset

test_la_key = "newcastle"


@pytest.fixture
def pop():
    return PopulationDataset()


@pytest.fixture
def school():
    return SchoolDataset()


@pytest.fixture
def datasets(pop, school):
    return [pop, school]


class TestDatasetGroup:
    @pytest.fixture
    def group_empty(self):
        return DatasetGroup()

    @pytest.fixture
    def group_data(self, datasets):
        return DatasetGroup(datasets=datasets, name="NAME")

    def test_init_defaults(self, group_empty):
        assert isinstance(group_empty, DatasetGroup)
        assert group_empty.datasets == {}
        assert group_empty.name == ""

    def test_init_datasets(self, group_data, sample_params):
        assert group_data.name == "NAME"
        assert len(group_data.datasets) == 2
        assert len(group_data.datasets["population"]) == sample_params["total"]["n_oa"]
        assert len(group_data.datasets["school"]) == sample_params["total"]["n_school"]

    def test_get(self, group_data):
        assert isinstance(group_data["population"], PopulationDataset)

    def test_set(self, group_empty, pop, sample_params):
        with pytest.raises(ValueError):
            group_empty[""] = pop
        group_empty["population"] = pop
        assert isinstance(group_empty["population"], PopulationDataset)
        assert len(group_empty["population"]) == sample_params["total"]["n_oa"]

    def test_repr(self, group_data):
        assert repr(group_data) == (
            "DatasetGroup(NAME): 2 datasets ('population', 'school')"
        )

    def test_add_dataset(self, group_empty, pop, sample_params):
        group_empty.add_dataset(pop)
        assert isinstance(group_empty["population"], PopulationDataset)
        assert len(group_empty["population"]) == sample_params["total"]["n_oa"]

    def test_len(self, group_empty, group_data):
        assert len(group_empty) == 0
        assert len(group_data) == 2

    def test_n_sites(self, group_data, sample_params):
        assert group_data.n_sites == sample_params["total"]["n_oa"]


class TestLocalAuthority:
    @pytest.fixture
    def la_empty(self, sample_params):
        return LocalAuthority(sample_params[test_la_key]["lad20cd"])

    @pytest.fixture
    def la_data(self, sample_params, datasets):
        return LocalAuthority(sample_params[test_la_key]["lad20cd"], datasets)

    def test_init_defaults(self, la_empty, sample_params):
        assert isinstance(la_empty, LocalAuthority)
        assert la_empty.lad20cd == sample_params[test_la_key]["lad20cd"]

    def test_init_datasets(self, la_data, sample_params):
        assert la_data.lad20cd == sample_params[test_la_key]["lad20cd"]
        assert len(la_data.datasets) == 2
        assert len(la_data.datasets["population"]) == sample_params[test_la_key]["n_oa"]
        assert len(la_data.datasets["school"]) == sample_params[test_la_key]["n_school"]

    def test_set(self, la_empty, pop, sample_params):
        with pytest.raises(ValueError):
            la_empty[""] = pop
        la_empty["population"] = pop
        assert isinstance(la_empty["population"], PopulationDataset)
        assert len(la_empty["population"]) == sample_params[test_la_key]["n_oa"]

    def test_repr(self, la_data, sample_params):
        assert repr(la_data) == (
            f"LocalAuthority: {sample_params[test_la_key]['lad20nm']} "
            f"({sample_params[test_la_key]['lad20cd']}):\n"
            f"- {sample_params[test_la_key]['n_oa']} output areas\n"
            f"- 2 datasets ('population', 'school')"
        )

    def test_n_oa11cd(self, la_empty, sample_params):
        assert la_empty.n_oa11cd == sample_params[test_la_key]["n_oa"]

    def test_to_oa_dataset_defaults(self, la_data, sample_params):
        la_oa = la_data.to_oa_dataset()
        assert "population" in la_oa.datasets and "school" in la_oa.datasets
        for _, d in la_oa.datasets.items():
            assert isinstance(d, OADataset)
            assert len(d) == sample_params[test_la_key]["n_oa"]
            np.testing.assert_array_equal(d.values.index, la_oa.oa11cd)

    def test_to_oa_dataset_weights(self, la_empty, sample_params):
        la_empty.add_dataset(HealthDataset())

        path = Path(__file__).parent / "../../sample/data/raw/population_total.csv"
        weights = pd.read_csv(path).set_index("oa11cd")["population"]
        la_oa = la_empty.to_oa_dataset(weights)
        assert isinstance(la_oa["health"], OADataset)
        assert len(la_oa["health"]) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(la_oa["health"].values.index, la_oa.oa11cd)

        la_oa_noweight = la_empty.to_oa_dataset(None)
        assert len(la_oa_noweight["health"]) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(
            la_oa_noweight["health"].values.index, la_oa.oa11cd
        )
        assert not la_oa_noweight["health"].values.equals(la_oa["health"].values)

    def test_la_shape(self, la_empty, sample_params):
        assert isinstance(la_empty.la_shape, pd.Series)
        assert "geometry" in la_empty.la_shape
        assert la_empty.la_shape.name == sample_params[test_la_key]["lad20cd"]

    def test_oa_shapes(self, la_empty, sample_params):
        assert isinstance(la_empty.oa_shapes, OABoundaryDataset)
        assert len(la_empty.oa_shapes) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(la_empty.oa_shapes.values.index, la_empty.oa11cd)

    def test_oa_centroids(self, la_empty, sample_params):
        assert isinstance(la_empty.oa_centroids, CentroidDataset)
        assert len(la_empty.oa_centroids) == sample_params[test_la_key]["n_oa"]
        np.testing.assert_array_equal(
            la_empty.oa_centroids.values.index, la_empty.oa11cd
        )

    def test_lad20nm(self, la_empty, sample_params):
        assert la_empty.lad20nm == sample_params[test_la_key]["lad20nm"]
