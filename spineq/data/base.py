from copy import deepcopy

import geopandas as gpd
import pandas as pd

from spineq.mappings import la_to_lsoas, lsoa_to_oas, point_to_oa


class Dataset:
    def __init__(self, name, values, index=None, title="", description=""):
        self.name = name
        self.values = values
        if index:
            self.values = self.values.set_index(index)
        self.title = title
        self.description = description

    def __getitem__(self, name):
        return self.values[name]

    def __len__(self):
        return len(self.values)

    def __repr__(self):
        return f"{type(self).__name__}: {self.name} ({len(self)} rows)"

    @classmethod
    def read_pandas(cls, name, path, read_kwargs=None, **kwargs):
        values = pd.read_csv(path, **(read_kwargs or {}))
        return cls(name, values, **kwargs)

    @classmethod
    def read_geopandas(cls, name, path, read_kwargs=None, **kwargs):
        values = gpd.read_file(path, **(read_kwargs or {}))
        return cls(name, values, **kwargs)

    def to_oa_dataset(self, *args, **kwargs):
        raise NotImplementedError(
            "Use a subclass of Dataset that implements the to_oa_dataset method"
        )

    def filter_la(self, *args, **kwargs):
        raise NotImplementedError(
            "Use a subclass of Dataset that implements the filter_la method"
        )


class PointDataset(Dataset):
    def to_oa_dataset(self, func="sum"):
        values = self.values.copy(deep=True).reset_index(drop=True)
        for i in range(len(values)):
            values.loc[i, "oa11cd"] = point_to_oa(values.loc[i, "geometry"])

        values = values.groupby("oa11cd").agg(func)

        return OADataset(
            self.name, values, title=self.title, description=self.description
        )

    def filter_la(self, la):
        filtered = deepcopy(self)
        filtered.values = filtered.values[
            filtered.values["geometry"].within(la.la_shape["geometry"])
        ]
        if not self.description:
            self.description = la.lad20cd
        return filtered


class OADataset(Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, index="oa11cd", **kwargs)

    def to_oa_dataset(self):
        return deepcopy(self)

    def filter_la(self, la):
        filtered = deepcopy(self)
        filtered.values = filtered.values[filtered.values.index.isin(la.oa11cd)]
        if not self.description:
            self.description = la.lad20cd
        return filtered


class LSOADataset(Dataset):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, index="lsoa11cd", **kwargs)

    def to_oa_dataset(self, oa_weights=None):
        values = []
        for lsoa11cd in self.values.index:
            if oa_weights:
                oas = lsoa_to_oas(lsoa11cd)
                weights = oa_weights.loc[oas] / oa_weights.loc[oas].sum()
                values.append(weights * self.values.loc[lsoa11cd])
            else:
                values.append(self.values.loc[lsoa11cd])
        values = pd.concat(values)

        return OADataset(
            self.name, values, title=self.title, description=self.description
        )

    def filter_la(self, la):
        lsoa11cd = la_to_lsoas(la.lad20cd)
        filtered = deepcopy(self)
        filtered.values = filtered.values[filtered.values.index.isin(lsoa11cd)]
        if not self.description:
            self.description = la.lad20cd
        return filtered
