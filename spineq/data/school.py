from copy import deepcopy

import geopandas as gpd

from spineq.data.base import PointDataset
from spineq.data.fetcher import download_schools

_default_title = "Education Establishments"


class SchoolDataset(PointDataset):
    def __init__(self, name="", title="", description=""):
        # TODO LA filter
        values = gpd.GeoDataFrame(download_schools())
        values["geometry"] = gpd.points_from_xy(
            values["Easting"], values["Northing"], crs="EPSG:27700"
        )
        super().__init__(
            name or "school",
            values,
            title=title or _default_title,
            description=description,
        )

    # TODO Consider overriding to_oa_dataset including extracting numeric columns

    def number_of_pupils(self, title=""):
        num_pupils = deepcopy(self)
        num_pupils.values = num_pupils[["NumberOfPupils"]]
        if title:
            num_pupils.title = title
        if (not num_pupils.title) or (num_pupils.title == _default_title):
            num_pupils.title = "Number of Pupils"
        return num_pupils
