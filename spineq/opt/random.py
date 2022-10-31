import numpy as np
from tqdm import trange

from spineq.opt.opt import Optimisation
from spineq.opt.result import PopulationResult


class Random(Optimisation):
    def __init__(self, population_size):
        self.population_size = population_size

    def run(self, objectives, n_sensors) -> PopulationResult:
        result = PopulationResult(objectives, n_sensors, self.population_size)
        return self.update(result)

    def update(self, result) -> PopulationResult:
        population = np.random.randint(
            result.objectives.coverage.n_sites,
            size=(self.population_size, result.objectives.coverage.n_sites),
        )
        total_coverage = [
            result.objectives.fitness(population[i, :])
            for i in trange(self.population_size)
        ]
        return PopulationResult(
            result.objectives,
            result.n_sensors,
            self.population_size,
            population=population,
            total_coverage=total_coverage,
        )
