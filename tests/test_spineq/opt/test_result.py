import numpy as np
import pytest

from spineq.data.census import WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.data.school import SchoolDataset
from spineq.opt.coverage import BinaryCoverage
from spineq.opt.objectives import Column, CombinedObjectives, Objectives
from spineq.opt.result import PopulationResult, Result, SingleNetworkResult

test_la_key = "gateshead"


@pytest.fixture
def la(sample_params):
    return LocalAuthority(
        sample_params[test_la_key]["lad20cd"],
        datasets=[WorkplaceDataset(), SchoolDataset()],
    ).to_oa_dataset()


@pytest.fixture
def columns():
    return [
        Column("workplace", "workers", 0.3),
        Column("school", "NumberOfPupils", 0.7),
    ]


@pytest.fixture
def cov(la):
    return BinaryCoverage.from_la(la, 2000)


@pytest.fixture
def n_sensors():
    return 10


class TestResult:
    @pytest.fixture
    def objectives(self, la, columns, cov):
        return Objectives(la, columns, cov)

    def test_init(self, objectives, n_sensors):
        r = Result(objectives, n_sensors)
        assert r.objectives == objectives
        assert r.n_sensors == n_sensors


class TestSingleNetworkResult:
    @pytest.fixture
    def objectives(self, la, columns, cov):
        return CombinedObjectives(la, columns, cov)

    def test_init_defaults(self, objectives, n_sensors):
        r = SingleNetworkResult(objectives, n_sensors)
        assert r.objectives == objectives
        assert r.n_sensors == n_sensors
        np.testing.assert_array_equal(r.sensors, np.zeros(objectives.coverage.n_sites))
        assert r.total_coverage == 0

    def test_init_values(self, objectives, n_sensors):
        sensors = np.zeros(objectives.coverage.n_sites)
        sensors[:n_sensors] = 1
        r = SingleNetworkResult(
            objectives, n_sensors, sensors=sensors, total_coverage=0.5
        )
        np.testing.assert_array_equal(r.sensors, sensors)
        assert r.total_coverage == 0.5


class TestPopulationResult:
    @pytest.fixture
    def objectives(self, la, columns, cov):
        return Objectives(la, columns, cov)

    @pytest.fixture
    def population_size(self):
        return 50

    def test_init_defaults(self, objectives, n_sensors, population_size):
        r = PopulationResult(objectives, n_sensors, population_size)
        assert r.objectives == objectives
        assert r.n_sensors == n_sensors
        assert r.population_size == population_size
        np.testing.assert_array_equal(
            r.population, np.zeros((population_size, objectives.coverage.n_sites))
        )
        np.testing.assert_array_equal(
            r.total_coverage, np.zeros((population_size, objectives.n_obj))
        )

    def test_init_values(self, objectives, n_sensors, population_size):
        population = np.zeros((population_size, objectives.coverage.n_sites))
        population[:, :n_sensors] = 1
        total_coverage = np.ones((population_size, objectives.n_obj))
        r = PopulationResult(
            objectives,
            n_sensors,
            population_size,
            population=population,
            total_coverage=total_coverage,
        )
        np.testing.assert_array_equal(r.population, population)
        np.testing.assert_array_equal(r.total_coverage, total_coverage)
