"""Utility functions used by other files.
"""
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon


def distance_matrix(x1, y1, x2=None, y2=None):
    """Generate a matrix of distances between a number of locations. Either
    pairwise distances between all locations in one set of x and y coordinates,
    or pairwise distances between one set of x,y coordinates (x1, y1) and
    another set of coordinates (x2,y2)

    Arguments:
        x1 {list-like} -- x coordinate for each location
        y1 {list-like} -- y coordinate for each location
        x2 {list-like} -- x coordinate for each location
        y2 {list-like} -- y coordinate for each location

    Returns:
        numpy array -- 2D matrix of distance between location i and location j,
        for each i and j.
    """

    coords_1 = np.array([x1, y1]).T

    if x2 is not None and y2 is not None:
        # calculate distances between two sets of coordinates
        coords_2 = np.array([x2, y2]).T

        dist_sq = np.sum(
            (coords_1[:, np.newaxis, :] - coords_2[np.newaxis, :, :]) ** 2, axis=-1
        )

    elif (x2 is None and y2 is not None) or (y2 is None and x2 is not None):
        raise ValueError("x2 and y2 both must be defined or undefined.")

    else:
        # calculate distances distances between points in one set of coordinates
        dist_sq = np.sum(
            (coords_1[:, np.newaxis, :] - coords_1[np.newaxis, :, :]) ** 2, axis=-1
        )

    distances = np.sqrt(dist_sq)

    return distances


def coverage_matrix(x1, y1, x2=None, y2=None, theta=1):
    """Generate a matrix of coverages for a number of locations

    Arguments:
        x {list-like} -- x coordinate for each location
        y {list-like} -- y coordinate for each location

    Keyword Arguments:
        theta {numeric} -- decay rate (default: {1})

    Returns:
        numpy array -- 2D matrix of coverage at each location i due to a
        sensor placed at another location j.
    """
    distances = distance_matrix(x1, y1, x2=x2, y2=y2)
    return np.exp(-distances / theta)


def coverage_from_sensors(sensors, coverage_matrix):
    # only keep coverages due to output areas where a sensor is present
    mask_cov = np.multiply(coverage_matrix, sensors[np.newaxis, :])
    # coverage at each output area = coverage due to nearest sensor
    max_mask_cov = np.max(mask_cov, axis=1)
    return max_mask_cov


def square_grid(xlim: list, ylim: list, grid_size: float):
    """Generate flat lists of x and y coordinates for points in a square grid.

    Parameters
    ----------
    xlim : list
        min and max x coordinate to generate grid points between
    ylim : list
        min and max y coordinate to generate grid points between
    grid_size : float
        distance between grid points (default: {100})

    Returns
    -------
    (np.Array, np.Array)
       x and y coordinates for points in the grid
    """
    # make a range of x and y locations for grid points
    x_range = np.arange(xlim[0], xlim[1] + grid_size, grid_size)
    y_range = np.arange(ylim[0], ylim[1] + grid_size, grid_size)

    # create flattened list of x, y coordinates for full grid
    grid_x, grid_y = np.meshgrid(x_range, y_range)
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()
    return grid_x, grid_y


def coverage_grid(sensors, xlim, ylim, grid_size=100, theta=500):
    """Generate a square grid of points and calculate coverage at each point
    due to the closest sensor.

    Arguments:
        sensors {numpy array} -- array of x,y sensor locations with shape
        (n_sensors, 2).
        xlim {list} -- min and max x coordinate to generate grid points between
        ylim {list} -- min and max y coordinate to generate grid points between

    Keyword Arguments:
        grid_size {float} -- distance between grid points (default: {100})
        theta {int} -- decay rate for coverage metric (default: {500})

    Returns:
        grid_cov -- GeoDataFrame of grid squares and coverage values.
    """
    # make a range of x and y locations for grid points
    grid_x, grid_y = square_grid(xlim, ylim, grid_size)

    # coverage at each grid point due to each sensor
    grid_cov = coverage_matrix(
        grid_x, grid_y, x2=sensors[:, 0], y2=sensors[:, 1], theta=theta
    )
    # max coverage at each grid point (due to nearest sensor)
    grid_cov = grid_cov.max(axis=1)

    polygons = [
        Polygon(
            [
                (x - grid_size / 2, y - grid_size / 2),
                (x + grid_size / 2, y - grid_size / 2),
                (x + grid_size / 2, y + grid_size / 2),
                (x - grid_size / 2, y + grid_size / 2),
            ]
        )
        for x, y in zip(grid_x, grid_y)
    ]

    return gpd.GeoDataFrame({"geometry": polygons, "coverage": grid_cov})


def make_job_dict(job):
    """Construct a dictionary out of RQ job status/results.

    Arguments:
        job {RQ job} -- RQ job object

    Returns:
        dict -- json like dictionary of job status/results
    """
    status = job.get_status()
    call_str = job.get_call_string()
    result = job.result

    if "progress" in job.meta.keys():
        progress = job.meta["progress"]
    else:
        progress = 0

    if "status" in job.meta.keys():
        last_message = job.meta["status"]

    return {
        "job_id": job.id,
        "call_str": call_str,
        "status": status,
        "progress": progress,
        "last_message": last_message,
        "result": result,
    }


def make_age_range(min_age=0, max_age=90):
    """Create a pandas series of age weights as needed for the optimisation.
    Index is from 0 to 90 (inclusive), returns weight 1 for
    min_age <= age <= max_age and 0 for all other ages.

    Keyword Arguments:
        min_age {int} -- [description] (default: {0})
        max_age {int} -- [description] (default: {90})

    Returns:
        [type] -- [description]
    """
    age_weights = pd.Series(0, index=range(91))
    age_weights[(age_weights.index >= min_age) & (age_weights.index <= max_age)] = 1
    return age_weights
