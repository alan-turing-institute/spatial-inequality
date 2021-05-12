import numpy as np
import matplotlib.pyplot as plt

from spineq.data_fetcher import get_uo_sensors, get_oa_centroids, get_oa_shapes
from spineq.plotting import plot_coverage_grid
from spineq.utils import coverage_grid


def get_uo_sensor_dict(centroids=True):
    """
    Get list of sensor dictionaries (compatible with coverage and plotting
    functions) for sensors in the Urban Observatory network. If centroids
    is True return only the centroid of 
    """
    uo_sensors = get_uo_sensors()
    
    if centroids:
        sensor_oa = uo_sensors["oa11cd"].unique()
        oa_centroids = get_oa_centroids()
        sensor_dict = (
            oa_centroids[
                oa_centroids.index.isin(sensor_oa)
            ][["x", "y"]]
            .reset_index()
            .to_dict(orient="records")
        )
    else:
        sensor_dict = [
            {
                "oa11cd": row["oa11cd"],
                "x": row["geometry"].x,
                "y": row["geometry"].y
            }
            for idx, row in uo_sensors.iterrows()
        ]

    return sensor_dict
    

def plot_uo_coverage_grid(
    ax=None, title=None, grid_size=100, theta=500, legend=True, cmap="Greens"
):
    uo_sensors = get_uo_sensors()
    sensors = np.array([uo_sensors["geometry"].x, uo_sensors["geometry"].y]).T

    oa = get_oa_shapes()
    bounds = oa["geometry"].bounds
    xlim = (bounds["minx"].min(), bounds["maxx"].max())
    ylim =(bounds["miny"].min(), bounds["maxy"].max())

    grid_cov = coverage_grid(sensors, xlim, ylim, grid_size=grid_size, theta=theta)

    if title is None:
        title = "Urban Observatory: {} sensors in {} output areas".format(
            len(uo_sensors), uo_sensors["oa11cd"].nunique()
        )

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(15, 15))

    ax = plot_coverage_grid(
        grid_cov,
        ax=ax,
        title=title,
        cmap=cmap,
        legend=legend,
    )

    return ax
