import geopandas as gpd

from spineq.data.base import PointDataset
from spineq.data.fetcher import download_schools


class SchoolDataset(PointDataset):
    def __init__(self, name="", title="", description=""):
        values = gpd.GeoDataFrame(download_schools())
        values["geometry"] = gpd.points_from_xy(
            values["Easting"], values["Northing"], crs="EPSG:27700"
        )
        super().__init__(
            name or "school",
            values,
            title=title or "Education Establishments",
            description=description,
        )
