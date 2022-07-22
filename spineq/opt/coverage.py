import numpy as np

from spineq.utils import distance_matrix


class Coverage:
    def coverage(self, sensors):
        raise NotImplementedError(
            "Use a Coverage subclass that implements the coverage method"
        )

    @classmethod
    def from_la(cls, la):
        raise NotImplementedError(
            "Use a Coverage subclass that implements the from_la method"
        )


class DistanceMatrixCoverage(Coverage):
    def __init__(self, x_sensors, y_sensors, x_sites=None, y_sites=None):
        self.distances = distance_matrix(x_sensors, y_sensors, x_sites, y_sites)

    @classmethod
    def from_la(cls, la):
        return cls(la.oa_centroids.values["x"], la.oa_centroids.values["y"])

    def coverage(self, sensors):
        # only keep coverages due to sites where a sensor is present
        if not hasattr(self, "coverage_matrix"):
            raise NotImplementedError(
                "Use a DitanceMatrixCoverage subclass that creates a coverage_matrix"
            )
        mask_cov = np.multiply(self.coverage_matrix, sensors[:, np.newaxis])
        # coverage at each site = coverage due to nearest sensor
        return np.max(mask_cov, axis=0)


class BinaryCoverage(DistanceMatrixCoverage):
    # 1 if within radius, else 0
    def __init__(self, x_sensors, y_sensors, radius, x_sites=None, y_sites=None):
        super().__init__(x_sensors, y_sensors, x_sites, y_sites)
        self.radius = radius
        self.coverage_matrix = (self.distances < radius).astype(int)

    @classmethod
    def from_la(cls, la, radius):
        return cls(la.oa_centroids.values["x"], la.oa_centroids.values["y"], radius)


class ExponentialCoverage(DistanceMatrixCoverage):
    # exp(-d/theta)
    def __init__(self, x_sensors, y_sensors, theta, x_sites=None, y_sites=None):
        super().__init__(x_sensors, y_sensors, x_sites, y_sites)
        self.theta = theta
        self.coverage_matrix = np.exp(-self.distances / theta)

    @classmethod
    def from_la(cls, la, theta):
        return cls(la.oa_centroids.values["x"], la.oa_centroids.values["y"], theta)
