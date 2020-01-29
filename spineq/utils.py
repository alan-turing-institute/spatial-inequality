
import numpy as np
import geopandas as gpd

from .data_fetcher import get_data


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
        
        dist_sq = np.sum((coords_1[:, np.newaxis, :] -
                          coords_2[np.newaxis, :, :]) ** 2,
                          axis=-1)
    
    elif (x2 is None and y2 is not None) or (y2 is None and x2 is not None):
        raise ValueError("x2 and y2 both must be defined or undefined.")
    
    else:
        # calculate distances distances between points in one set of coordinates
        dist_sq = np.sum((coords_1[:, np.newaxis, :] -
                         coords_1[np.newaxis, :, :]) ** 2,
                         axis = -1)
    
    distances = np.sqrt(dist_sq)
    
    return distances


def satisfaction_scalar(distance, theta=1):
    """Calculate "satisfaction" due to a sensor placed a given distance away,
    where satisfaction is defined as exp(-distance/theta).
    
    Arguments:
        distance {numeric} -- distance to sensor.
    
    Keyword Arguments:
        theta {numeric} -- decay rate (default: {1})
    
    Returns:
        float -- satisfaction value.
    """
    return np.exp(-distance / theta)


# vectorized satisfaction function
satisfaction = np.vectorize(satisfaction_scalar)


def satisfaction_matrix(x1, y1, x2=None, y2=None, theta=1):
    """Generate a matrix of satisfactions for a number of locations
    
    Arguments:
        x {list-like} -- x coordinate for each location
        y {list-like} -- y coordinate for each location
    
    Keyword Arguments:
        theta {numeric} -- decay rate (default: {1})
    
    Returns:
        numpy array -- 2D matrix of satisfaction at each location i due to a
        sensor placed at another location j.
    """
    return satisfaction(distance_matrix(x1, y1, x2=x2, y2=y2), theta=theta)
