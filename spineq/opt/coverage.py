import numpy as np

from spineq.utils import distance_matrix


class Coverage:
    def coverage(self, sensors):
        raise NotImplementedError(
            "Use a Coverage subclass that implements the coverage method"
        )


class DistanceMatrixCoverage(Coverage):
    def __init__(self, la):
        self.distances = distance_matrix(
            la.oa_centroids.values["x"], la.oa_centroids.values["y"]
        )

    def coverage(self, sensors):
        # only keep coverages due to sites where a sensor is present
        if not hasattr(self, "coverage_matrix"):
            raise NotImplementedError(
                "Use a DitanceMatrixCoverage subclass that creates a coverage_matrix"
            )
        mask_cov = np.multiply(self.coverage_matrix, sensors[np.newaxis, :])
        # coverage at each site = coverage due to nearest sensor
        return np.max(mask_cov, axis=1)


class BinaryCoverage(DistanceMatrixCoverage):
    # 1 if within radius, else 0
    def __init__(self, la, radius):
        super().__init__(la)
        self.coverage_matrix = (self.distances < radius).astype(int)


class ExponentialCoverage(DistanceMatrixCoverage):
    # exp(-d/theta)
    def __init__(self, la, theta):
        super().__init__(la)
        self.coverage_matrix = np.exp(-self.distances / theta)