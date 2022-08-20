import numpy as np
import pygmo as pg
import pytest

from spineq.data.census import WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.data.school import SchoolDataset
from spineq.opt.coverage import BinaryCoverage
from spineq.opt.objectives import Column, CombinedObjectives
from spineq.opt.pygmo import CoverageProblem, PyGMOResult

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
    # small radius so only OA with sensor in gets coverage
    return BinaryCoverage.from_la(la, 1)


@pytest.fixture
def objectives(la, columns, cov):
    return CombinedObjectives(la, columns, cov)


@pytest.fixture
def n_sensors():
    return 3


@pytest.fixture
def population_size():
    return 20


class TestPyGMOResult:
    @pytest.fixture
    def algorithm(self):
        return pg.algorithm(uda=pg.sga(gen=10))

    @pytest.fixture
    def problem(self, objectives, n_sensors):
        return pg.problem(CoverageProblem(objectives, n_sensors))

    @pytest.fixture
    def population(self, problem, population_size):
        return pg.population(prob=problem, size=population_size)

    @pytest.fixture
    def result(self, algorithm, population):
        return PyGMOResult(algorithm, population)

    def test_init(self, result, algorithm, population, n_sensors, population_size):
        assert result.n_sensors == n_sensors
        assert isinstance(result.objectives, CombinedObjectives)
        assert result.population == population
        assert result.algorithm == algorithm
        assert result.total_coverage.shape == (population_size, 1)

    def test_all_sensors(self, result, population_size, n_sensors):
        assert result.all_sensors.shape == (population_size, n_sensors)

    def test_all_coverage(self, result, population_size):
        assert result.all_coverage.shape == (population_size, 1)

    def test_best_coverage(self, result):
        assert result.best_coverage == result.all_coverage.max()

    def test_best_sensors(self, result):
        idx = result.all_coverage.argmax()
        np.testing.assert_array_equal(result.best_sensors, result.all_sensors[idx, :])


class TestPyGMO:
    def test_init(self):
        ...

    def test_run(self):
        ...

    def test_update(self):
        ...


class TestCoverageProblem:
    def test_init(self):
        ...

    def test_fitness(self):
        ...

    def test_get_bounds(self):
        ...

    def test_get_nobj(self):
        ...

    def test_get_nec(self):
        ...

    def test_get_nix(self):
        ...
