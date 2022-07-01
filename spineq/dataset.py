import geopandas as gpd
import pandas as pd


class Dataset:
    def __init__(self, name, values, index=None, title="", description=""):
        self.name = name
        self.values = values
        if index:
            self.values = self.values.set_index(index)
        self.title = title
        self.description = description

    @classmethod
    def read_pandas(cls, name, path, read_kwargs=None, data_kwargs=None):
        values = pd.read_csv(path, **(read_kwargs or {}))
        return cls(name, values, **(data_kwargs or {}))

    @classmethod
    def read_geopandas(cls, name, path, read_kwargs=None, data_kwargs=None):
        values = gpd.read_file(path, **(read_kwargs or {}))
        return cls(name, values, **(data_kwargs or {}))


class PointDataset(Dataset):
    def to_oa_dataset(self, agg="sum"):
        values = ...
        return OADataset(self.name, values)

    def filter_la(self, la):
        pass


class RegionDataset(Dataset):
    def __init__(self, name, values, match_id, **kwargs):
        self.match_id = match_id  # oa11cd/lsoa11cd...
        super().__init__(name, values, **kwargs)

    def filter_la(self, la):
        pass

    @classmethod
    def read_pandas(cls, name, path, match_id, read_kwargs=None, data_kwargs=None):
        data_kwargs = {} or data_kwargs
        data_kwargs["match_id"] = match_id
        return super().read_pandas(name, path, read_kwargs, data_kwargs)

    @classmethod
    def read_geopandas(cls, name, path, match_id, read_kwargs=None, data_kwargs=None):
        data_kwargs = {} or data_kwargs
        data_kwargs["match_id"] = match_id
        return super().read_geopandas(name, path, read_kwargs, data_kwargs)


class OADataset(RegionDataset):
    def __init__(self, name, values, **kwargs):
        super().__init__(name, values, "oa11cd", **kwargs)

    def to_oa_dataset(self):
        return self


class LSOADataset(RegionDataset):
    def __init__(self, name, values, **kwargs):
        super().__init__(name, values, "lsoa11cd", **kwargs)

    def to_oa_dataset(self, agg="population"):
        values = ...
        return OADataset(self.name, values)
