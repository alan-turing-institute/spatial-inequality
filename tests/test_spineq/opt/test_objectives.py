import pytest

from spineq.data.census import WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.data.school import SchoolDataset
from spineq.opt.coverage import BinaryCoverage
from spineq.opt.objectives import Column, Objectives

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
    return BinaryCoverage.from_la(la, 500)


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

    def test_weights(self):
        ...

    def test_oa_coverage(self):
        ...

    def test_fitness(self):
        ...


class TestCombinedObjectives:
    def test_objective_weights(self):
        ...

    def test_weights(self):
        ...
