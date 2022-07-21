import numpy as np
import pandas as pd
import pytest

from spineq.data.school import SchoolDataset


class TestSchoolDataset:
    @pytest.fixture
    def dataset(self):
        return SchoolDataset()

    def test_init_defaults(self, dataset, sample_params):
        assert isinstance(dataset, SchoolDataset)
        assert dataset.name == "school"
        assert dataset.title == "Education Establishments"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params["total"]["n_school"]
        assert len(dataset.values.columns) == 39

    def test_init_all(self, sample_params):
        dataset = SchoolDataset(
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, SchoolDataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, pd.DataFrame)
        assert len(dataset) == sample_params["total"]["n_school"]
        assert len(dataset.values.columns) == 39

    def test_number_of_pupils_defaults(self, dataset):
        num_pupils = dataset.number_of_pupils()
        assert isinstance(num_pupils, SchoolDataset)
        assert num_pupils.title == "Number of Pupils"
        assert len(dataset) == len(num_pupils)
        np.testing.assert_array_equal(num_pupils.values.columns, ["NumberOfPupils"])

    def test_number_of_pupils_title(self, dataset):
        num_pupils = dataset.number_of_pupils(title="TITLE")
        assert isinstance(num_pupils, SchoolDataset)
        assert num_pupils.title == "TITLE"
        assert len(dataset) == len(num_pupils)
        np.testing.assert_array_equal(num_pupils.values.columns, ["NumberOfPupils"])
