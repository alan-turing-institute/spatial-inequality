from copy import deepcopy

import numpy as np
import pygmo as pg

from spineq.opt.opt import Optimisation
from spineq.opt.result import PopulationResult


class PyGMOResult(PopulationResult):
    def __init__(
        self,
        algorithm,
        pg_population,
    ):
        coverage = pg_population.problem.extract(CoverageProblem)
        super().__init__(
            coverage.objectives,
            coverage.n_sensors,
            population_size=pg_population.get_x().shape[0],
            population=pg_population.get_x(),
            total_coverage=-pg_population.get_f(),
        )
        self.algorithm = algorithm
        self.pg_population = pg_population

    @property
    def best_coverage(self):
        return -self.pg_population.champion_f

    @property
    def best_sensors(self):
        return self.pg_population.champion_x


class PyGMO(Optimisation):
    def __init__(self, algorithm, population_size, verbosity=1):
        self.verbosity = verbosity
        self.algorithm = algorithm
        self.population_size = population_size

    def run(self, objectives, n_sensors) -> PyGMOResult:
        problem = pg.problem(CoverageProblem(objectives, n_sensors))
        # Create algorithm to solve problem with
        algorithm = pg.algorithm(uda=self.algorithm)
        algorithm.set_verbosity(self.verbosity)

        # population of problems
        pg_population = pg.population(prob=problem, size=self.population_size)

        result = PyGMOResult(algorithm, pg_population)

        # solve problem
        return self.update(result)

    def update(self, result) -> PyGMOResult:
        result = deepcopy(result)
        pg_population = result.algorithm.evolve(result.pg_population)
        result.pg_population = pg_population
        return result


class CoverageProblem:
    def __init__(self, objectives, n_sensors):
        self.objectives = objectives
        self.n_sensors = n_sensors

    def fitness(self, sensors_idx):
        """Objective function to minimise."""
        sensors = np.zeros(self.objectives.coverage.n_sites)
        sensors[sensors_idx.astype(int)] = 1
        fit = -self.objectives.fitness(sensors)
        return [fit] if isinstance(fit, float) else fit

    def get_bounds(self):
        """Min and max value for each parameter."""
        return (
            [0] * self.n_sensors,
            [self.objectives.coverage.n_sites - 1] * self.n_sensors,
        )

    def get_nobj(self):
        """Number of objectives"""
        return self.objectives.n_obj

    def get_nec(self):
        """Number of equality constraints."""
        return 0

    def get_nix(self):
        """Number of integer dimensions."""
        return self.n_sensors
