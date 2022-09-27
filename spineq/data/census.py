from copy import deepcopy

import geopandas as gpd
import pandas as pd

from spineq.data.base import LSOADataset, OADataset
from spineq.data.fetcher import (
    get_lsoa_health,
    get_oa_centroids,
    get_oa_population,
    get_oa_shapes,
    get_oa_workplace,
)


class CentroidDataset(OADataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        centroids = get_oa_centroids(lad20cd)
        values = gpd.GeoDataFrame(
            centroids,
            crs="EPSG:27700",
            geometry=gpd.points_from_xy(centroids["x"], centroids["y"]),
        )
        super().__init__(
            name or "centroids",
            values.reset_index(),
            title=title or "Output Area Centroids",
            description=description,
        )


class OABoundaryDataset(OADataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        boundaries = get_oa_shapes(lad20cd)
        super().__init__(
            name or "oa_boundary",
            boundaries.reset_index(),
            title=title or "Output Area Boundaries",
            description=description,
        )


class PopulationDataset(OADataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        values = get_oa_population(lad20cd).reset_index()
        super().__init__(
            name or "population",
            values,
            title=title or "Number of Residents",
            description=description,
        )

    def filter_age(self, low=0, high=90, name="", title="", description=""):
        filt_self = deepcopy(self)
        filt_self.values = filt_self.values.loc[
            :,
            (self.values.columns >= low) & (self.values.columns <= high),
        ]
        if name:
            filt_self.name = name
        else:
            pre = filt_self.name or "population"
            filt_self.name = f"{pre}_{low}_to_{high}"
        if title:
            filt_self.title = title
        else:
            pre = filt_self.title or "Number of Residents"
            filt_self.title = f"{pre} Between {low} and {high} Years Old"
        if description:
            filt_self.description = description

        return filt_self

    def to_total(self):
        self_total = deepcopy(self)
        self_total.values = pd.DataFrame({"total": self_total.values.sum(axis=1)})
        return self_total


class WorkplaceDataset(OADataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        values = get_oa_workplace(lad20cd).reset_index()
        super().__init__(
            name or "workplace",
            values,
            title=title or "Number of Workers",
            description=description,
        )


class HealthDataset(LSOADataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        values = get_lsoa_health(lad20cd)
        super().__init__(
            name or "health",
            values,
            title=title or "Long-term Health Issues and Disabilty",
            description=description,
        )
