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
def sample_3x3():
    return {
        "x": [0, 3, 6],
        "y": [0, 4, 8],
        "d": np.array([[0, 5, 10], [5, 0, 5], [10, 5, 0]]),
    }


@pytest.fixture
def sample_2x3():
    return {
        "x_sensors": [0, 6],
        "y_sensors": [0, 8],
        "x_sites": [0, 3, 6],
        "y_sites": [0, 4, 8],
        "d": np.array([[0, 5, 10], [10, 5, 0]]),
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

    def test_init_2x3(self, sample_2x3):
        cov = DistanceMatrixCoverage(
            sample_2x3["x_sensors"],
            sample_2x3["y_sensors"],
            sample_2x3["x_sites"],
            sample_2x3["y_sites"],
        )
        np.testing.assert_array_almost_equal(cov.distances, sample_2x3["d"])

    def test_coverage(self, cov):
        with pytest.raises(NotImplementedError):
            cov.coverage(np.array([0, 1, 0]))


class TestBinaryCoverage:
    @pytest.fixture
    def cov_3x3(self, sample_3x3):
        return BinaryCoverage(sample_3x3["x"], sample_3x3["y"], 6)

    @pytest.fixture
    def cov_2x3(self, sample_2x3):
        return BinaryCoverage(
            sample_2x3["x_sensors"],
            sample_2x3["y_sensors"],
            6,
            sample_2x3["x_sites"],
            sample_2x3["y_sites"],
        )

    def test_init(self, la):
        cov = BinaryCoverage.from_la(la, 500)
        assert isinstance(cov, BinaryCoverage)
        assert cov.radius == 500
        assert isinstance(cov.coverage_matrix, np.ndarray)

    def test_coverage_matrix_3x3(self, cov_3x3, sample_3x3):
        np.testing.assert_array_equal(
            cov_3x3.coverage_matrix, sample_3x3["d"] < cov_3x3.radius
        )

    def test_coverage_3x3(self, cov_3x3):
        np.testing.assert_array_equal(
            cov_3x3.coverage(np.array([0, 0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_equal(
            cov_3x3.coverage(np.array([1, 0, 0])), np.array([1, 1, 0])
        )
        np.testing.assert_array_equal(
            cov_3x3.coverage(np.array([0, 0, 1])), np.array([0, 1, 1])
        )
        np.testing.assert_array_equal(
            cov_3x3.coverage(np.array([1, 1, 1])), np.array([1, 1, 1])
        )

    def test_init_2x3(self, cov_2x3, sample_2x3):
        np.testing.assert_array_equal(
            cov_2x3.coverage_matrix, sample_2x3["d"] < cov_2x3.radius
        )

    def test_coverage_2x3(self, cov_2x3):
        np.testing.assert_array_equal(
            cov_2x3.coverage(np.array([0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_equal(
            cov_2x3.coverage(np.array([1, 0])), np.array([1, 1, 0])
        )
        np.testing.assert_array_equal(
            cov_2x3.coverage(np.array([0, 1])), np.array([0, 1, 1])
        )
        np.testing.assert_array_equal(
            cov_2x3.coverage(np.array([1, 1])), np.array([1, 1, 1])
        )


class TestExponentialCoverage:
    @pytest.fixture
    def cov_2x3(self, sample_2x3):
        return ExponentialCoverage(
            sample_2x3["x_sensors"],
            sample_2x3["y_sensors"],
            6,
            sample_2x3["x_sites"],
            sample_2x3["y_sites"],
        )

    @pytest.fixture
    def cov_3x3(self, sample_3x3):
        return ExponentialCoverage(sample_3x3["x"], sample_3x3["y"], 2)

    def test_init(self, la):
        cov = ExponentialCoverage.from_la(la, 500)
        assert isinstance(cov, ExponentialCoverage)
        assert cov.theta == 500
        assert isinstance(cov.coverage_matrix, np.ndarray)

    def test_coverage_matrix_3x3(self, cov_3x3, sample_3x3):
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage_matrix, np.exp(-sample_3x3["d"] / cov_3x3.theta)
        )

    def test_coverage_3x3(self, cov_3x3):
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage(np.array([0, 0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage(np.array([1, 1, 1])), np.array([1, 1, 1])
        )
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage(np.array([1, 0, 0])),
            np.array([1, cov_3x3.coverage_matrix[0, 1], cov_3x3.coverage_matrix[0, 2]]),
        )
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage(np.array([0, 0, 1])),
            np.array([cov_3x3.coverage_matrix[2, 0], cov_3x3.coverage_matrix[2, 1], 1]),
        )
        np.testing.assert_array_almost_equal(
            cov_3x3.coverage(np.array([1, 0, 1])),
            np.array([1, cov_3x3.coverage_matrix[0, 1], 1]),
        )

    def test_init_2x3(self, cov_2x3, sample_2x3):
        np.testing.assert_array_almost_equal(
            cov_2x3.coverage_matrix, np.exp(-sample_2x3["d"] / cov_2x3.theta)
        )

    def test_coverage_2x3(self, cov_2x3):
        np.testing.assert_array_almost_equal(
            cov_2x3.coverage(np.array([0, 0])), np.array([0, 0, 0])
        )
        np.testing.assert_array_almost_equal(
            cov_2x3.coverage(np.array([1, 1])),
            np.array([1, cov_2x3.coverage_matrix[1, 1], 1]),
        )
        np.testing.assert_array_almost_equal(
            cov_2x3.coverage(np.array([1, 0])),
            np.array([1, cov_2x3.coverage_matrix[0, 1], cov_2x3.coverage_matrix[0, 2]]),
        )
        np.testing.assert_array_almost_equal(
            cov_2x3.coverage(np.array([0, 1])),
            np.array([cov_2x3.coverage_matrix[1, 0], cov_2x3.coverage_matrix[1, 1], 1]),
        )
