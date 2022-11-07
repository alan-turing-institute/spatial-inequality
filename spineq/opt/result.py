import numpy as np


class Result:
    def __init__(self, objectives, n_sensors):
        self.objectives = objectives
        self.n_sensors = n_sensors


class SingleNetworkResult(Result):
    def __init__(self, objectives, n_sensors, sensors=None, total_coverage=0):
        super().__init__(objectives, n_sensors)
        if sensors is None:
            sensors = np.zeros(self.objectives.coverage.n_sites)
        self.sensors = sensors
        self.total_coverage = total_coverage


class PopulationResult(Result):
    def __init__(
        self,
        objectives,
        n_sensors,
        population_size,
        population=None,
        total_coverage=None,
    ):
        super().__init__(objectives, n_sensors)
        if population is None:
            population = np.zeros((population_size, self.objectives.coverage.n_sites))
        if total_coverage is None:
            total_coverage = np.zeros((population_size, self.objectives.n_obj))
        self.population_size = population_size
        self.population = population
        self.total_coverage = total_coverage

    def get_single_result(self, idx):
        return SingleNetworkResult(
            self.objectives,
            self.n_sensors,
            self.objectives.idx_to_sensors(self.population[idx, :].astype(int)),
            self.total_coverage[idx],
        )

    def best_idx(self, obj_idx=0):
        if len(self.objectives) > 0:
            return self.total_coverage[:, obj_idx].argmax()
        return self.total_coverage.argmax()

    def best_result(self, obj_idx=0) -> SingleNetworkResult:
        return SingleNetworkResult(
            self.objectives,
            self.n_sensors,
            self.objectives.idx_to_sensors(self.best_sensors(obj_idx).astype(int)),
            self.best_coverage()[obj_idx],
        )

    def best_coverage(self):
        if len(self.objectives) > 0:
            return self.total_coverage.max(axis=0)
        return self.total_coverage.max()

    def best_sensors(self, obj_idx=0):
        return self.population[self.best_idx(obj_idx), :]
