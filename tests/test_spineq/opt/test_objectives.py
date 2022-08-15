import numpy as np
import pandas as pd
import pytest

from spineq.data.census import WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.data.school import SchoolDataset
from spineq.opt.coverage import BinaryCoverage
from spineq.opt.objectives import Column, CombinedObjectives, Objectives

test_la_key = "newcastle"


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


class TestColumn:
    def test_init_defaults(self):
        o = Column("DATASET", "COLUMN")
        assert isinstance(o, Column)
        assert o.dataset == "DATASET"
        assert o.column == "COLUMN"
        assert o.weight == 1.0
        assert o.label == "DATASET_COLUMN"

    def test_init_label(self):
        o = Column("DATASET", "COLUMN", 1.0, "LABEL")
        assert o.label == "LABEL"


class TestObjectives:
    @pytest.fixture
    def objs(self, la, columns, cov):
        return Objectives(la, columns, cov)

    def test_init_defaults(self, objs, columns, cov):
        assert isinstance(objs, Objectives)
        assert objs.objectives == columns
        assert objs.coverage == cov
        assert objs.norm is True

    def test_init_norm(self, la, columns, cov):
        assert Objectives(la, columns, cov, False).norm is False

    def test_weights(self, objs, la):
        assert isinstance(objs.weights, np.ndarray)
        assert objs.weights.shape == (la.n_oa11cd, len(objs))
        np.testing.assert_array_almost_equal(objs.weights.sum(axis=0), (1, 1))
        # E00042480: work: 188, school: 197
        # Total Newcastle: work: 22556, school: 5274
        idx = pd.Index(la.oa11cd).get_loc("E00042480")
        assert objs.weights[idx, 0] == pytest.approx(188 / 22556)
        assert objs.weights[idx, 1] == pytest.approx(197 / 5274)

    def test_oa_coverage(self, objs, la):
        sensors = np.ones(la.n_oa11cd)
        np.testing.assert_array_equal(objs.oa_coverage(sensors), 1)
        sensors = np.zeros(la.n_oa11cd)
        np.testing.assert_array_equal(objs.oa_coverage(sensors), 0)
        # sensor at E00042480 covers E00042735 (if cov distance is 2000m)
        idx_sensor = pd.Index(la.oa11cd).get_loc("E00042480")
        idx_covered = pd.Index(la.oa11cd).get_loc("E00042735")
        sensors = np.zeros(la.n_oa11cd)
        sensors[idx_sensor] = 1
        exp_coverage = np.zeros(la.n_oa11cd)
        exp_coverage[idx_sensor] = 1
        exp_coverage[idx_covered] = 1
        np.testing.assert_array_equal(objs.oa_coverage(sensors), exp_coverage)

    def test_fitness(self, objs, la):
        sensors = np.ones(la.n_oa11cd)
        np.testing.assert_array_almost_equal(objs.fitness(sensors), [1, 1])
        sensors = np.zeros(la.n_oa11cd)
        np.testing.assert_array_almost_equal(objs.fitness(sensors), [0, 0])
        # sensor at E00042480 covers E00042735 (if cov distance is 2000m)
        # E00042480: work: 188, school: 197
        # E00042735:  work: 139, school: 0
        # Total Newcastle: work: 22556, school: 5274
        sensors[pd.Index(la.oa11cd).get_loc("E00042480")] = 1
        np.testing.assert_array_almost_equal(
            objs.fitness(sensors), [(188 + 139) / 22556, 197 / 5274]
        )


class TestCombinedObjectives:
    @pytest.fixture
    def objs(self, la, columns, cov):
        return CombinedObjectives(la, columns, cov)

    def test_init(self, objs, columns, cov):
        assert isinstance(objs, CombinedObjectives)
        assert objs.objectives == columns
        assert objs.coverage == cov
        assert objs.norm is True

    def test_objective_weights(self, objs):
        np.testing.assert_array_equal(objs.objective_weights, [0.3, 0.7])

    def test_weights(self, objs, la):
        # sensor at E00042480 covers E00042735 (if cov distance is 2000m)
        # E00042480: work: 188, school: 197
        # E00042735:  work: 139, school: 0
        # Total Newcastle: work: 22556, school: 5274
        sensors = np.zeros(la.n_oa11cd)
        sensors[pd.Index(la.oa11cd).get_loc("E00042480")] = 1
        assert objs.fitness(sensors) == pytest.approx(
            0.3 * (188 + 139) / 22556 + 0.7 * 197 / 5274
        )
