from spineq.opt.result import Result


class Optimisation:
    def run(self, objectives, n_sensors) -> Result:
        raise NotImplementedError(
            "Use an optimisation subclass that implements the run method"
        )

    def update(self, result: Result) -> Result:
        raise NotImplementedError(
            "Use an optimisation subclass that implements the update method"
        )
