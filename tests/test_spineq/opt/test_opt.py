import pytest

from spineq.opt.opt import Optimisation


class TestOptimisation:
    @pytest.fixture
    def opt(self):
        return Optimisation()

    def test_init(self, opt):
        assert isinstance(opt, Optimisation)

    def test_run(self, opt):
        with pytest.raises(NotImplementedError):
            opt.run(0, 1)

    def test_update(self, opt):
        with pytest.raises(NotImplementedError):
            opt.update(0)
