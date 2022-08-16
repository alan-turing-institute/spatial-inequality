import numpy as np
import pygmo as pg

from spineq.opt.opt import Optimisation


class Genetic(Optimisation):
    def __init__(self, uda, population_size, verbosity=1):
        self.verbosity = verbosity
        self.uda = uda
        self.population_size = population_size

    def run(self, objectives, n_sensors):
        prob = pg.problem(CoverageProblem(objectives, n_sensors))
        # Create algorithm to solve problem with
        algo = pg.algorithm(uda=self.uda)
        algo.set_verbosity(self.verbosity)

        # population of problems
        pop = pg.population(prob=prob, size=self.population_size)

        # solve problem
        pop = algo.evolve(pop)
        return pop, algo


class CoverageProblem:
    def __init__(self, objectives, n_sensors):
        self.objectives = objectives
        self.n_sensors = n_sensors

    def fitness(self, sensors_idx):
        """Objective function to minimise."""
        # Construct sensors vector from indices
        sensors = np.zeros(self.objectives.coverage.n_sites)
        sensors[sensors_idx.astype(int)] = 1
        # calculate coverage
        return -self.objectives.fitness(sensors)

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

    def gradient(self, x):
        return pg.estimate_gradient_h(lambda x: self.fitness(x), x)


def extract_all(pop):
    """Return all solutions from a population.

    Parameters
    ----------
    pop : pg.population
        Population of problem solutions

    Returns
    -------
    numpy.array, numpy.array
        Candidate scores and solutions
    """
    return pop.get_f(), pop.get_x()


def extract_champion(pop):
    """Return best solution from a population. Works for single-objective problems only.

    Parameters
    ----------
    pop : pg.population
        Population of problem solutions

    Returns
    -------
    float, numpy.array
        Best candidate's score and solution.
    """
    return pop.champion_f, pop.champion_x
