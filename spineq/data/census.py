from copy import deepcopy

from spineq.data.base import LSOADataset, OADataset
from spineq.data.fetcher import get_lsoa_health, get_oa_population, get_oa_workplace


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
