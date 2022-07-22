import numpy as np
import pytest

from spineq.data.group import LocalAuthority
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
def sample_xyd():
    return {
        "x": [0, 3, 6],
        "y": [0, 4, 8],
        "d": np.array([[0, 5, 10], [5, 0, 5], [10, 5, 0]]),
    }


class TestCoverage:
    def test_coverage(self):
        cov = Coverage()
        with pytest.raises(NotImplementedError):
            cov.coverage(np.array([0, 1, 0]))

    def test_from_la(self, la):
        with pytest.raises(NotImplementedError):
            Coverage.from_la(la)


class TestDistanceMatrixCoverage:
    @pytest.fixture
    def cov(self, la):
        return DistanceMatrixCoverage.from_la(la)

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
    @pytest.fixture
    def cov(self, sample_xyd):
        return BinaryCoverage(sample_xyd["x"], sample_xyd["y"], 6)

    def test_init(self, la):
        cov = BinaryCoverage.from_la(la, 500)
        assert isinstance(cov, BinaryCoverage)
        assert cov.radius == 500
        assert isinstance(cov.coverage_matrix, np.ndarray)

    def test_coverage_matrix(self, cov, sample_xyd):
        np.testing.assert_array_almost_equal(
            cov.coverage_matrix, sample_xyd["d"] < cov.radius
        )

    def test_coverage(self, cov):
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([0, 0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([1, 0, 0])), np.array([1, 1, 0])
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([0, 0, 1])), np.array([0, 1, 1])
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([1, 1, 1])), np.array([1, 1, 1])
        )


class TestExponentialCoverage:
    @pytest.fixture
    def cov(self, sample_xyd):
        return ExponentialCoverage(sample_xyd["x"], sample_xyd["y"], 2)

    def test_init(self, la):
        cov = ExponentialCoverage.from_la(la, 500)
        assert isinstance(cov, ExponentialCoverage)
        assert cov.theta == 500
        assert isinstance(cov.coverage_matrix, np.ndarray)

    def test_coverage_matrix(self, cov, sample_xyd):
        np.testing.assert_array_almost_equal(
            cov.coverage_matrix, np.exp(-sample_xyd["d"] / cov.theta)
        )

    def test_coverage(self, cov):
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([0, 0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([1, 1, 1])), np.array([1, 1, 1])
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([1, 0, 0])),
            np.array([1, cov.coverage_matrix[0, 1], cov.coverage_matrix[0, 2]]),
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([0, 0, 1])),
            np.array([cov.coverage_matrix[2, 0], cov.coverage_matrix[2, 1], 1]),
        )
        np.testing.assert_array_almost_equal(
            cov.coverage(np.array([1, 0, 1])),
            np.array([1, cov.coverage_matrix[0, 1], 1]),
        )
