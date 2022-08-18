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
