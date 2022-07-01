import geopandas as gpd
import pandas as pd

from spineq.oa_lookup import la_to_lsoas, point_to_oa


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
    def to_oa_dataset(self, column, func="sum", **kwargs):
        values = self.values.copy(deep=True).reset_index(drop=True)
        for i in range(len(values)):
            values.loc[i, "oa11cd"] = point_to_oa(values.loc[i, "geometry"])

        values = values.groupby("oa11cd")[column].agg(func)
        return OADataset(self.name, values, **kwargs)

    def filter_la(self, la):
        self.values = self.values[self.values["geometry"].isin(la.la_shape)]


class OADataset(Dataset):
    def to_oa_dataset(self):
        return self

    def filter_la(self, la):
        self.values = self.values[self.values["oa11cd"].isin(la.oa11cd)]


class LSOADataset(Dataset):
    def to_oa_dataset(self, agg="population"):
        values = ...
        return OADataset(self.name, values)

    def filter_la(self, la):
        lsoa11cd = la_to_lsoas(la.lad20cd)
        self.values = self.values[self.values["lsoa11cd"].isin(lsoa11cd)]
