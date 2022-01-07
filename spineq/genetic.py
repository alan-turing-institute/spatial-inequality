import numpy as np
import pygmo as pg

from spineq.utils import coverage_matrix, coverage_from_sensors


class OptimiseCoveragePyGMO:
    def __init__(self, oa_x, oa_y, oa_weight, n_sensors, theta):
        self.n_sensors = n_sensors
        self.n_locations = len(oa_x)
        if isinstance(oa_weight, dict):
            self.n_obj = len(oa_weight)
            self.oa_weight = list(oa_weight.values())
        else:
            self.n_obj = 1
            self.oa_weight = [oa_weight]
        self.coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    def fitness(self, sensors_idx):
        """Objective function to minimise."""
        # Construct sensors vector from indices
        sensors = np.zeros(self.n_locations)
        sensors[sensors_idx.astype(int)] = 1
        # calculate coverage at each OA due to these sensors
        sensor_cov = coverage_from_sensors(sensors, self.coverage)
        # coverage of objective = weighted average of OA coverages due to sensors
        return [-1 * np.average(sensor_cov, weights=w) for w in self.oa_weight]

    def get_bounds(self):
        """Min and max value for each parameter."""
        return ([0] * self.n_sensors, [self.n_locations - 1] * self.n_sensors)

    def get_nobj(self):
        """Number of objectives"""
        return self.n_obj

    def get_nec(self):
        """Number of equality constraints."""
        return 0

    def get_nix(self):
        """Number of integer dimensions."""
        return self.n_sensors

    def gradient(self, x):
        return pg.estimate_gradient_h(lambda x: self.fitness(x), x)


def build_problem(
    optimisation_inputs,
    n_sensors=20,
    theta=500,
):
    return pg.problem(
        OptimiseCoveragePyGMO(
            optimisation_inputs["oa_x"],
            optimisation_inputs["oa_y"],
            optimisation_inputs["oa_weight"],
            n_sensors,
            theta,
        )
    )


def run_problem(prob, uda=pg.sga(gen=100), population_size=100, verbosity=1):
    # Create algorithm to solve problem with
    algo = pg.algorithm(uda=uda)
    algo.set_verbosity(verbosity)

    # population of problems
    pop = pg.population(prob=prob, size=population_size)

    # solve problem
    pop = algo.evolve(pop)
    return pop


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
