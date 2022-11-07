from spineq.data.base import PointDataset
from spineq.data.fetcher import get_uo_sensors


class UODataset(PointDataset):
    def __init__(self, lad20cd=None, name="", title="", description=""):
        values = get_uo_sensors(lad20cd=lad20cd)
        super().__init__(
            name or "urban_observatory",
            values,
            title=title or "Urban Observatory",
            description=description or "Air Quality Sensors",
        )
