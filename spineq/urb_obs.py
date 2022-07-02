import matplotlib.pyplot as plt
import numpy as np

from spineq.data.fetcher import get_oa_centroids, get_oa_shapes, get_uo_sensors
from spineq.plotting import plot_coverage_grid
from spineq.utils import coverage_grid


def get_uo_sensor_dict(lad20cd, centroids=True, uo_sensors=None):
    """
    Get list of sensor dictionaries (compatible with coverage and plotting
    functions) for sensors in the Urban Observatory network. If centroids
    is True return only the centroid of
    """
    if uo_sensors is None:
        uo_sensors = get_uo_sensors(lad20cd)

    if centroids:
        sensor_oa = uo_sensors["oa11cd"].unique()
        oa_centroids = get_oa_centroids(lad20cd)
        sensor_dict = (
            oa_centroids[oa_centroids.index.isin(sensor_oa)][["x", "y"]]
            .reset_index()
            .to_dict(orient="records")
        )
    else:
        sensor_dict = [
            {"oa11cd": row["oa11cd"], "x": row["geometry"].x, "y": row["geometry"].y}
            for idx, row in uo_sensors.iterrows()
        ]

    return sensor_dict


def plot_uo_coverage_grid(
    lad20cd,
    uo_sensors=None,
    ax=None,
    title=None,
    grid_size=100,
    theta=500,
    legend=True,
    cmap="Greens",
):
    if uo_sensors is None:
        uo_sensors = get_uo_sensors(lad20cd)
    sensors = np.array([uo_sensors["geometry"].x, uo_sensors["geometry"].y]).T

    oa = get_oa_shapes(lad20cd)
    bounds = oa["geometry"].bounds
    xlim = (bounds["minx"].min(), bounds["maxx"].max())
    ylim = (bounds["miny"].min(), bounds["maxy"].max())

    grid_cov = coverage_grid(sensors, xlim, ylim, grid_size=grid_size, theta=theta)

    if title is None:
        title = "Urban Observatory: {} sensors in {} output areas".format(
            len(uo_sensors), uo_sensors["oa11cd"].nunique()
        )

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(15, 15))

    ax = plot_coverage_grid(
        lad20cd,
        grid_cov,
        ax=ax,
        title=title,
        cmap=cmap,
        legend=legend,
    )

    return ax
