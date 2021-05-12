import numpy as np
import pygmo as pg

from spineq.utils import coverage_matrix, coverage_from_sensors


class OptimiseCoveragePyGMO:
    def __init__(self, oa_x, oa_y, oa_weight, n_sensors, theta):
        print(oa_weight)
        self.n_sensors = n_sensors
        self.n_locations = len(oa_x)
        if isinstance(oa_weight, dict):
            self.n_obj = len(oa_weight)
            self.oa_weight = oa_weight.values()
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
        return ([0]*self.n_sensors, [self.n_locations-1]*self.n_sensors)

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


def run():
    from spineq.optimise import get_optimisation_inputs
    data = get_optimisation_inputs()

    prob = pg.problem(OptimiseCoveragePyGMO(
        data["oa_x"],
        data["oa_y"],
        data["oa_weight"],
        20,
        500
    ))
    print(prob)

    # Create algorithm to solve problem with
    algo = pg.algorithm(uda=pg.sga(gen=100))
    algo.set_verbosity(1)
    print(algo)

    # population of problems
    pop = pg.population(prob=prob, size=100)

    # solve problem
    pop = algo.evolve(pop)
    return pop


def evaluate(pop):
    print("f evals", pop.problem.get_fevals())
    print("g evals", pop.problem.get_gevals())

    # extract results
    fits, vectors = pop.get_f(), pop.get_x()
    # extract non-dominated fronts
    ndf, dl, dc, ndr = pg.fast_non_dominated_sorting(fits)