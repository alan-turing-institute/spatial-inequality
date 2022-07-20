from copy import deepcopy

import geopandas as gpd

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
        values = deepcopy(self.values).loc[
            :,
            (self.values.columns >= low) & (self.values.columns <= high),
        ]
        # reset index as OADataset constructor expects oa11cd column to be presents
        values = values.reset_index()
        if not name:
            name = f"population_{low}_to_{high}"
        if not title:
            title = f"Residents Between {low} and {high} Years Old"
        return PopulationDataset(
            name,
            values,
            title=title,
            description=description or self.description,
        )

    def to_total(self):
        self_total = deepcopy(self)
        self_total.values = self_total.values.sum(axis=1)
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
