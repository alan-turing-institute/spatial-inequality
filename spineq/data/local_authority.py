from functools import cached_property

from spineq.data.base import LSOADataset
from spineq.data.census import CentroidDataset, OABoundaryDataset
from spineq.data.fetcher import get_la_shape
from spineq.mappings import la_to_oas, lad20cd_to_lad20nm


class LocalAuthority:
    def __init__(self, lad20cd, datasets=None):
        self.lad20cd = lad20cd
        self.oa11cd = la_to_oas(lad20cd)
        self.datasets = {}
        if datasets:
            for d in datasets:
                self.add_dataset(d)

    def __getitem__(self, name):
        return self.datasets[name]

    def __setitem__(self, dataset, name):
        dataset = dataset.filter_la(self)
        self.datasets[name] = dataset

    def __repr__(self):
        return (
            f"{type(self).__name__}: {self.lad20nm} ({self.lad20cd}):\n"
            f"- {len(self)} output areas\n"
            f"- {len(self.datasets)} datasets {tuple(self.datasets.keys())}\n"
        )

    def __len__(self):
        return len(self.oa11cd)

    def add_dataset(self, dataset, name=None):
        if not name:
            name = dataset.name
        self.__setitem__(dataset, name)

    def to_oa_dataset(self, oa_weights=None):
        datasets = {}
        for name, d in self.datasets.items():
            if isinstance(d, LSOADataset):
                oa_dat = d.to_oa_dataset(oa_weights)
            else:
                oa_dat = d.to_oa_dataset()
            oa_dat.values = oa_dat.values.reindex(self.oa11cd)
            datasets[name] = oa_dat

        return LocalAuthority(self.lad20cd, datasets)

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
