from functools import cached_property

from spineq.data_fetcher import get_la_shape, get_oa_centroids, get_oa_shapes
from spineq.dataset import LSOADataset
from spineq.mappings import la_to_oas


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
        dataset = ...  # TODO: Match index
        self.datasets[name] = dataset

    def add_dataset(self, dataset, name=None):
        if not name:
            name = dataset.name
        self.__setitem__(dataset, name)

    def to_oa_dataset(self, oa_weights=None):
        datasets = []
        for d in datasets.values():
            if isinstance(d, LSOADataset):
                datasets.append(d.to_oa_dataset(oa_weights))
            else:
                datasets.append(d.to_oa_dataset())

    @cached_property
    def la_shape(self):
        return get_la_shape(self.lad20cd)

    @cached_property
    def oa_shapes(self):
        return get_oa_shapes(self.lad20cd)

    @cached_property
    def oa_centroids(self):
        return get_oa_centroids(self.lad20cd)
