import matplotlib.pyplot as plt
import numpy as np

from spineq.data.fetcher import get_oa_centroids, get_uo_sensors
from spineq.data.urb_obs import UODataset
from spineq.opt.objectives import Objectives
from spineq.opt.result import SingleNetworkResult
from spineq.plot.plotting import plot_coverage_grid, plot_optimisation_result
from spineq.utils import coverage_grid


def get_uo_sensor_dict(lad20cd, centroids=True, uo_sensors=None):
    """
    Get list of sensor dictionaries (compatible with coverage and plotting
    functions) for sensors in the Urban Observatory network. If centroids
    is True return only the centroid of
    """
    if uo_sensors is None:
        uo_sensors = get_uo_sensors(lad20cd)

    if not centroids:
        return [
            {"oa11cd": row["oa11cd"], "x": row["geometry"].x, "y": row["geometry"].y}
            for idx, row in uo_sensors.iterrows()
        ]

    sensor_oa = uo_sensors["oa11cd"].unique()
    oa_centroids = get_oa_centroids(lad20cd)
    return (
        oa_centroids[oa_centroids.index.isin(sensor_oa)][["x", "y"]]
        .reset_index()
        .to_dict(orient="records")
    )


def plot_uo_coverage_grid(
    la,
    uo_sensors=None,
    ax=None,
    title=None,
    grid_size=100,
    theta=500,
    legend=True,
    cmap="Greens",
):
    if uo_sensors is None:
        uo_sensors = UODataset(la.lad20cd)
    sensors = np.array(
        [uo_sensors.values["geometry"].x, uo_sensors.values["geometry"].y]
    ).T

    bounds = la.oa_shapes.values["geometry"].bounds
    xlim = (bounds["minx"].min(), bounds["maxx"].max())
    ylim = (bounds["miny"].min(), bounds["maxy"].max())

    grid_cov = coverage_grid(sensors, xlim, ylim, grid_size=grid_size, theta=theta)

    if title is None:
        title = (
            f"Urban Observatory: {len(uo_sensors)} sensors in "
            f"{uo_sensors['oa11cd'].nunique()} output areas"
        )

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(15, 15))

    ax = plot_coverage_grid(
        la,
        grid_cov,
        ax=ax,
        title=title,
        cmap=cmap,
        legend=legend,
    )

    return ax


def plot_uo_coverage_oa(
    uo_sensors: UODataset,
    objectives: Objectives,
    ax=None,
    title=None,
    legend=True,
    cmap="Greens",
):
    sensors = objectives.names_to_sensors(uo_sensors.values["oa11cd"].unique())
    total_coverage = objectives.fitness(sensors)
    result = SingleNetworkResult(
        objectives, len(uo_sensors.values), sensors, total_coverage
    )

    if title is None:
        title = (
            f"Urban Observatory: {len(uo_sensors.values)} sensors in "
            f"{uo_sensors.values['oa11cd'].nunique()} output areas"
        )

    return plot_optimisation_result(
        result, title=title, ax=ax, legend=legend, cmap=cmap, show=False
    )
