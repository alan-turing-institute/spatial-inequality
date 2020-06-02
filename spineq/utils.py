"""Utility functions used by other files.
"""
import numpy as np
import geopandas as gpd
import pandas as pd


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
