from functools import cached_property

import pandas as pd

from spineq.data.base import LSOADataset
from spineq.data.census import CentroidDataset, OABoundaryDataset, OADataset
from spineq.data.fetcher import get_la_shape
from spineq.mappings import la_to_oas, lad20cd_to_lad20nm


class DatasetGroup:
    def __init__(self, datasets=None, name="", site_names=None):
        self.name = name
        self.site_names = pd.Index(site_names) if site_names is not None else None
        self.datasets = {}
        if datasets:
            for d in datasets:
                self.add_dataset(d)

    def __getitem__(self, name):
        return self.datasets[name]

    def __setitem__(self, name, dataset):
        if not name:
            raise ValueError("name must be defined")
        self.datasets[name] = dataset

    def __repr__(self):
        return (
            f"{type(self).__name__}({self.name}): "
            f"{len(self)} datasets {tuple(self.datasets.keys())}"
        )

    def __len__(self):
        return len(self.datasets)

    @property
    def n_sites(self):
        return len(self.datasets[next(iter(self.datasets))])

    def add_dataset(self, dataset):
        self.__setitem__(dataset.name, dataset)

    def site_idx(self, name):
        return self.site_names.get_loc(name)


class LocalAuthority(DatasetGroup):
    def __init__(self, lad20cd, datasets=None):
        self.lad20cd = lad20cd
        self.oa11cd = la_to_oas(lad20cd)
        super().__init__(datasets=datasets, name=self.lad20cd, site_names=self.oa11cd)

    def __setitem__(self, name, dataset):
        if not name:
            raise ValueError("name must be defined")
        dataset = dataset.filter_la(self)
        if isinstance(dataset, OADataset):
            dataset.values = dataset.values.reindex(self.oa11cd)
        self.datasets[name] = dataset

    def __repr__(self):
        return (
            f"{type(self).__name__}: {self.lad20nm} ({self.lad20cd}):\n"
            f"- {self.n_oa11cd} output areas\n"
            f"- {len(self)} datasets {tuple(self.datasets.keys())}"
        )

    def to_oa_dataset(self, oa_weights=None):
        datasets = []
        for _, d in self.datasets.items():
            if isinstance(d, LSOADataset):
                oa_dat = d.to_oa_dataset(oa_weights)
            else:
                oa_dat = d.to_oa_dataset()
            oa_dat.values = oa_dat.values.reindex(self.oa11cd)
            datasets.append(oa_dat)

        return LocalAuthority(self.lad20cd, datasets)

    @property
    def n_oa11cd(self):
        return len(self.oa11cd)

    @property
    def n_sites(self):
        return self.n_oa11cd

    @cached_property
    def la_shape(self):
        return get_la_shape(self.lad20cd)

    @cached_property
    def oa_shapes(self):
        boundaries = OABoundaryDataset(self.lad20cd)
        boundaries.values = boundaries.values.reindex(self.oa11cd)
        return boundaries

    @cached_property
    def oa_centroids(self):
        centroids = CentroidDataset(self.lad20cd)
        centroids.values = centroids.values.reindex(self.oa11cd)
        return centroids

    @cached_property
    def lad20nm(self):
        return lad20cd_to_lad20nm(self.lad20cd)
