import numpy as np

from spineq.opt.opt import Optimisation


class Greedy(Optimisation):
    def __init__(self, verbose=True, job=None, socket_io=None):
        self.verbose = verbose
        self.job = job
        self.socket_io = socket_io

    def run(self, objectives, n_sensors):
        # binary array - 1 if sensor at this location, 0 if not
        sensors = np.zeros(objectives.coverage.n_sites)

        # coverage obtained with each number of sensors
        placement_history = []
        coverage_history = []

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

            # initialise arrays to store best result so far
            best_total_coverage = 0
            best_sensors = sensors.copy()

            for site in range(objectives.coverage.n_sites):
                if sensors[site] == 1:
                    # already have a sensor here, so skip to next
                    continue
                new_sensors = sensors.copy()
                new_sensors[site] = 1

                new_coverage = objectives.fitness(sensors)

                if new_coverage > best_total_coverage:
                    # this site is the best site for next sensor found so far
                    best_new_site = site
                    best_sensors = new_sensors.copy()
                    best_total_coverage = new_coverage

            sensors = best_sensors.copy()
            placement_history.append(best_new_site)
            coverage_history.append(best_total_coverage)
            if self.verbose:
                print("coverage = {:.2f}".format(best_total_coverage))

        return {
            "sensors": sensors,
            "total_coverage": best_total_coverage,
            "placement_history": placement_history,
            "coverage_history": coverage_history,
        }
