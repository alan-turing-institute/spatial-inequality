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

    @property
    def best_idx(self):
        return self.total_coverage.argmax()

    @property
    def best_result(self) -> SingleNetworkResult:
        return SingleNetworkResult(
            self.objectives,
            self.n_sensors,
            self.objectives.idx_to_sensors(self.best_sensors.astype(int)),
            self.best_coverage,
        )

    @property
    def best_coverage(self):
        return self.total_coverage.max()

    @property
    def best_sensors(self):
        return self.population[self.best_idx, :]
