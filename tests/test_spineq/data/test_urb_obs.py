import geopandas as gpd

from spineq.data.urb_obs import UODataset


class TestUODataset:
    def test_init_defaults(self, sample_params):
        dataset = UODataset()
        assert isinstance(dataset, UODataset)
        assert dataset.name == "urban_observatory"
        assert dataset.title == "Urban Observatory"
        assert dataset.description == "Air Quality Sensors"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params["total"]["n_urb_obs"]
        assert len(dataset.values.columns) == 9

    def test_init_all(self, sample_params):
        dataset = UODataset(
            name="NAME",
            title="TITLE",
            description="DESCRIPTION",
        )
        assert isinstance(dataset, UODataset)
        assert dataset.name == "NAME"
        assert dataset.title == "TITLE"
        assert dataset.description == "DESCRIPTION"
        assert isinstance(dataset.values, gpd.GeoDataFrame)
        assert len(dataset) == sample_params["total"]["n_urb_obs"]
        assert len(dataset.values.columns) == 9
