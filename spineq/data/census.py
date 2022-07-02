from spineq.data.base import LSOADataset, OADataset


class PopulationDataset(OADataset):
    def __init__(self):
        super().__init__(...)


class WorkplaceDataset(OADataset):
    ...


class HealthDataset(LSOADataset):
    ...
