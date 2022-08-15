from dataclasses import dataclass
from typing import Any, Optional

import numpy as np

from spineq.data.group import DatasetGroup
from spineq.opt.coverage import Coverage
from spineq.utils import normalize


@dataclass
class Column:
    dataset: str
    column: str
    weight: float = 1.0
    label: Optional[str] = None
    fill_na: Optional[Any] = 0

    def __post_init__(self):
        if not self.label:
            self.label = f"{self.dataset}_{self.column}"


class Objectives:
    def __init__(
        self,
        datasets: DatasetGroup,
        objectives: list[Column],
        coverage: Coverage,
        norm: bool = True,
    ):
        self.objectives = objectives
        self.coverage = coverage
        self.norm = norm

        self.weights = np.full((datasets.n_sites, len(objectives)), np.nan)
        for i, obj in enumerate(objectives):
            self.weights[:, i] = datasets[obj.dataset][obj.column].fillna(obj.fill_na)
        if norm:
            self.weights = normalize(self.weights, axis=0)

    def __len__(self):
        return len(self.objectives)

    def oa_coverage(self, sensors):
        return self.coverage.coverage(sensors)

    def fitness(self, sensors):
        cov = self.oa_coverage(sensors)
        return (self.weights * cov[:, np.newaxis]).sum(axis=0)


class CombinedObjectives(Objectives):
    def __init__(
        self,
        datasets: DatasetGroup,
        objectives: list[Column],
        coverage: Coverage,
        norm: bool = True,
    ):
        super().__init__(datasets, objectives, coverage, norm=norm)
        self.objective_weights = np.array([obj.weight for obj in objectives])
        if norm:
            self.objective_weights = normalize(self.objective_weights)

        # weight for each OA is weighted sum of all objectives
        self.weights = (self.objective_weights * self.weights).sum(axis=1)

    def fitness(self, sensors):
        cov = self.oa_coverage(sensors)
        return (self.weights * cov).sum()
