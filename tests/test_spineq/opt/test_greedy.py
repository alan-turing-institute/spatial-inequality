import numpy as np
import pytest

from spineq.data.census import WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.data.school import SchoolDataset
from spineq.opt.coverage import BinaryCoverage
from spineq.opt.greedy import Greedy, GreedyResult
from spineq.opt.objectives import Column, CombinedObjectives

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
        Column("workplace", "workers", 1.0),
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


class TestGreedyResult:
    def test_init_defaults(self, objectives, n_sensors):
        r = GreedyResult(
            objectives,
            n_sensors,
        )
        assert r.n_sensors == n_sensors
        assert r.objectives == objectives
        assert r.placement_history == []
        assert r.coverage_history == []
        np.testing.assert_array_equal(r.sensors, np.zeros(objectives.coverage.n_sites))
        assert r.total_coverage == 0

    def test_init_values(self, objectives, n_sensors):
        sensors = np.zeros(objectives.coverage.n_sites)
        sensors[1] = 1
        r = GreedyResult(
            objectives,
            n_sensors,
            sensors=sensors,
            total_coverage=0.5,
            placement_history=[1],
            coverage_history=[0.5],
        )
        assert r.n_sensors == n_sensors
        assert r.objectives == objectives
        assert r.placement_history == [1]
        assert r.coverage_history == [0.5]
        np.testing.assert_array_equal(r.sensors, sensors)
        assert r.total_coverage == 0.5


class TestGreedy:
    @pytest.fixture
    def greedy(self):
        return Greedy()

    def test_init(self, greedy):
        assert greedy.verbose is True
        assert greedy.job is None
        assert greedy.socket_io is None

    def test_init_job(self):
        ...  # TODO

    def test_run(self, greedy, objectives, n_sensors):
        r = greedy.run(objectives, n_sensors)
        assert r.sensors.sum() == n_sensors
        assert 0 < r.total_coverage < 1
        assert len(r.placement_history) == n_sensors
        assert len(r.coverage_history) == n_sensors
        # E00041435 (1230, idx 4), E00166205 (1040, idx 10), E00041395 (280, idx 2)
        # total workers: 3227
        assert r.placement_history == [4, 10, 2]
        np.testing.assert_array_almost_equal(
            r.coverage_history,
            [1230 / 3227, (1230 + 1040) / 3227, (1230 + 1040 + 280) / 3227],
        )

    def test_update(self, greedy, objectives, n_sensors):
        r = greedy.run(objectives, n_sensors)
        new_r = greedy.update(r)
        assert new_r.sensors.sum() == n_sensors + 1
        assert 0 < new_r.total_coverage < 1
        assert new_r.total_coverage > r.total_coverage
        assert len(new_r.placement_history) == n_sensors + 1
        assert len(new_r.coverage_history) == n_sensors + 1
