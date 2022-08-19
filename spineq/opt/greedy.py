from copy import deepcopy

import numpy as np

from spineq.opt.opt import Optimisation
from spineq.opt.result import SingleNetworkResult


class GreedyResult(SingleNetworkResult):
    def __init__(
        self,
        objectives,
        n_sensors,
        sensors=None,
        total_coverage=0,
        placement_history=None,
        coverage_history=None,
    ):
        super().__init__(objectives, n_sensors, sensors, total_coverage)
        if placement_history is None:
            placement_history = []
        if coverage_history is None:
            coverage_history = []
        self.placement_history = placement_history  # order of placed sensors
        self.coverage_history = coverage_history  # total coverage after each sensor


class Greedy(Optimisation):
    def __init__(self, verbose=True, job=None, socket_io=None):
        self.verbose = verbose
        self.job = job
        self.socket_io = socket_io

    def run(self, objectives, n_sensors) -> GreedyResult:
        result = GreedyResult(objectives, n_sensors)

        for s in range(n_sensors):
            # greedily add sensors
            if self.verbose:
                print("Placing sensor", s + 1, "out of", n_sensors, "... ", end="")

            if self.job:
                self.job.meta["status"] = f"Placing sensor {s + 1} out of {n_sensors}"
                progress = 100 * s / n_sensors
                self.job.meta["progress"] = progress
                self.job.save_meta()
                if self.socket_io is not None:
                    self.socket_io.emit(
                        "jobProgress", {"job_id": self.job.id, "progress": progress}
                    )

            result = self.update(result)
            if self.verbose:
                print("coverage = {:.2f}".format(result.coverage_history[-1]))

        return result

    def update(self, result) -> GreedyResult:
        result = deepcopy(result)
        n_sites = len(result.sensors)
        new_coverages = np.zeros(n_sites)
        for site in range(n_sites):
            # try adding sensor at potential sensor site
            if result.sensors[site] == 1:
                # already have a sensor here, so skip to next
                continue

            new_sensors = result.sensors.copy()
            new_sensors[site] = 1
            new_coverages[site] = result.objectives.fitness(new_sensors)

        best_idx = new_coverages.argmax()
        best_coverage = new_coverages.max()
        result.placement_history.append(best_idx)
        result.coverage_history.append(best_coverage)
        result.total_coverage = best_coverage
        updated_sensors = result.sensors.copy()
        updated_sensors[best_idx] = 1
        result.sensors = updated_sensors
        return result
