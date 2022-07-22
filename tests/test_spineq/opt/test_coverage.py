import numpy as np
import pytest

from spineq.data.local_authority import LocalAuthority
from spineq.opt.coverage import (
    BinaryCoverage,
    Coverage,
    DistanceMatrixCoverage,
    ExponentialCoverage,
)

test_la_key = "gateshead"


@pytest.fixture
def la(sample_params):
    return LocalAuthority(sample_params[test_la_key]["lad20cd"])


@pytest.fixture
def radius():
    return 500


class TestCoverage:
    def test_coverage(self):
        cov = Coverage()
        with pytest.raises(NotImplementedError):
            cov.coverage(np.array([0, 1, 0]))


class TestDistanceMatrixCoverage:
    @pytest.fixture
    def cov(self, la):
        return DistanceMatrixCoverage(la)

    def test_init(self, cov, sample_params, la):
        assert isinstance(cov, DistanceMatrixCoverage)
        assert isinstance(cov.distances, np.ndarray)
        n_oa = sample_params[test_la_key]["n_oa"]
        assert cov.distances.shape == (n_oa, n_oa)
        oa_1_xy = la.oa_centroids.values.iloc[0].values
        oa_2_xy = la.oa_centroids.values.iloc[1].values
        distance = np.sqrt(
            (oa_1_xy[0] - oa_2_xy[0]) ** 2 + (oa_1_xy[1] - oa_2_xy[1]) ** 2
        )
        assert cov.distances[0, 1] == pytest.approx(distance)

    def test_coverage(self, cov):
        with pytest.raises(NotImplementedError):
            cov.coverage(np.array([0, 1, 0]))


class TestBinaryCoverage:
    def test_init(self, la, radius):
        cov = BinaryCoverage(la, radius)
        assert isinstance(cov, BinaryCoverage)
        ...  # TODO

    def test_coverage(self):
        ...  # TODO


class TestExponentialCoverage:
    def test_init(self, la, radius):
        cov = ExponentialCoverage(la, radius)
        assert isinstance(cov, ExponentialCoverage)
        ...  # TODO

    def test_coverage(self):
        ...  # TODO
