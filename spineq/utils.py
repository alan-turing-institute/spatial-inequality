
import numpy as np
import geopandas as gpd

from .data_fetcher import get_data


def distance_matrix(x, y):
    """Generate a matrix of distances between a number of locations.
    
    Arguments:
        x {list-like} -- x coordinate for each location
        y {list-like} -- y coordinate for each location
    
    Returns:
        numpy array -- 2D matrix of distance between location i and location j,
        for each i and j.
    """

    locations = np.array([x, y]).T
    
    dist_sq = np.sum((locations[:, np.newaxis, :] -
                      locations[np.newaxis, :, :]) ** 2,
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


def satisfaction_matrix(x, y, theta=1):
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
    return satisfaction(distance_matrix(x, y), theta)


def plot_sensors(sensors,
                 figsize=(20,20),
                 print_sensors=True,
                 theta=500):
    """
    Plot map with sensor locations (red points), output area centroids (black points),
    and satisfaction (shaded areas).
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import make_axes_locatable
    import contextily as ctx

    data = get_data()
    satisfaction = satisfaction_matrix(data["poi_x"],
                                       data["poi_y"],
                                       theta)
    poi_weight = data["poi_weight"]
    
    gdf = gpd.read_file("data/tyne_oa")
        
    # only keep satisfactions due to output areas where a sensor is present
    mask_sat = np.multiply(satisfaction, sensors[np.newaxis, :])

    # satisfaction at each output area = satisfaction due to nearest sensor
    max_mask_sat = np.max(mask_sat, axis=1)

    # population weighted average satisfaction
    avg_satisfaction = (poi_weight * max_mask_sat).sum() / poi_weight.sum()
    
    gdf["satisfaction"] = max_mask_sat

    # to make colorbar same size as graph:
    # https://www.science-emergence.com/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
    ax = plt.figure(figsize=figsize).gca()
    
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    ax = gdf.plot(column="satisfaction",
                  alpha=0.75,
                  cmap="YlGn", legend=True,
                  ax=ax, cax=cax)


    x = gdf[sensors == 1]["X"]
    y = gdf[sensors == 1]["Y"]
    ax.scatter(x, y, s=24, color='r')

    x = gdf[sensors == 0]["X"]
    y = gdf[sensors == 0]["Y"]
    ax.scatter(x, y, s=4, color='k')


    ctx.add_basemap(ax,
                    url="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
                    crs=gdf.crs)

    ax.set_axis_off()
    ax.set_title("n_sensors = {:.0f}, satisfaction = {:.2f}".format(sensors.sum(), avg_satisfaction),
                fontsize=20)
    
    # output areas with sensors
    if print_sensors:
        print("Output areas with sensors:",
              gdf[sensors == 1]["oa11cd"].values)
        
    plt.show()