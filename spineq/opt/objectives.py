class SingleObjective:
    # - Output area indices
    # - Output area weights (1 x n)
    #   - From dataset
    #   - with normalisation
    # - Coverage metric
    pass


class MultiObjectives:
    # - Output area indices
    # - Output area weights (k x n)
    # - Coverage metric
    # - Convert to single objective
    #   - weight for each objective
    #   - normalisation
    def __init__(self, objectives):
        self.objectives = objectives

    def to_single_objective(self, weights, norm=True):
        ...


# !!! THESE SHOULD BUILD ON LOCAL AUTHORITY CLASS?? !!!
