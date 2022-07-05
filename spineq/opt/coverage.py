# Output area centroids
#   - is a point dataset? -> Nope -> is a OADataset? -> Nope?

# Coverage metric
#   - contains e.g. coverage matrix (computed from centroids)
#   - Given sensor oa11cd -> value(s)


class Coverage:
    def __init__(self, data_sites, sensor_sites=None, **kwargs):
        self._precompute(data_sites, sensor_sites, **kwargs)

    def _precompute(self, data_sites, sensor_sites, *args, **kwargs):
        raise NotImplementedError(
            "Use a Coverage subclass that implements the _precompute method"
        )

    def coverage(self, sensors):
        raise NotImplementedError(
            "Use a Coverage subclass that implements the coverage method"
        )


class BinaryCoverage(Coverage):
    # 1 if within distance, else 0
    pass


class ExponentialCoverage(Coverage):
    # exp(-d/theta)
    pass
