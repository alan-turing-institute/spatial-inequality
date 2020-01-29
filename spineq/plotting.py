import numpy as np
import geopandas as gpd

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import contextily as ctx

from .utils import satisfaction_matrix
from .data_fetcher import get_data


def plot_sensors(sensors,
                 figsize=(20,20),
                 print_sensors=True,
                 theta=500):
    """
    Plot map with sensor locations (red points), output area centroids (black points),
    and satisfaction (shaded areas).
    """
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


def plot_coverage_grid(sensors, xlim, ylim,
                       grid_size=100, theta=500,
                       crs={'init': 'epsg:27700'},
                       threshold=0.25, alpha=0.75,
                       title="", figsize=(20,20),
                       vmin=0, vmax=1,
                       save_path=None):
    """Generate a square grid of points and show them on a map coloured by
    coverage due to the closest sensor to each grid point.
    
    Arguments:
        sensors {numpy array} -- array of x,y sensor locations with shape
        (n_sensors, 2).
        xlim {list} -- min and max x coordinate to generate grid points between
        ylim {list} -- min and max y coordinate to generate grid points between
    
    Keyword Arguments:
        grid_size {float} -- distance between grid points (default: {100})
        theta {int} -- decay rate for coverage metric (default: {500})
        crs {dict} -- coordinate reference system of sensor locations
        (default: {{'init': 'epsg:27700'}})
        threshold {float} -- only plot grid points with coverage above this
        value (default: {0.25})
        alpha {float} -- transparency of grid points (default: {0.75})
        title {str} -- plot title (default: {""})
        figsize {tuple} -- plot figure size (default: {(20,20)})
        vmin {float} -- min coverage value for colorbar range (default: {0})
        vmax {float} -- max coverage value for colorbar range (default: {1})
        save_path {str} -- path to save output plot or None to not save
        (default: {None})
    
    Returns:
        fig, ax -- matplotlib figure and axis objects for the created plot.
    """
    ###############
    # create grid #
    ###############
    # make a range of x and y locations for grid points
    x_range = np.arange(xlim[0], xlim[1]+grid_size, grid_size)
    y_range = np.arange(ylim[0], ylim[1]+grid_size, grid_size)
    
    # create flattened list of x, y coordinates for full grid
    grid_x, grid_y = np.meshgrid(x_range, y_range)
    grid_x = grid_x.flatten()
    grid_y = grid_y.flatten()
    
    # coverage at each grid point due to each sensor
    grid_cov = satisfaction_matrix(grid_x,
                                   grid_y,
                                   x2=sensors[:, 0],
                                   y2=sensors[:, 1],
                                   theta=theta)
    
    # max coverage at each grid point (due to nearest sensor)
    max_cell_cov = grid_cov.max(axis=1)
    
    # only plot grid points where coverage above threshold
    grid_x = grid_x[max_cell_cov > threshold]
    grid_y = grid_y[max_cell_cov > threshold]
    max_cell_cov = max_cell_cov[max_cell_cov > threshold]

    #############
    # make plot #
    #############
    fig, ax = plt.subplots(1, 1, figsize=figsize)

    # match colorbar axis height to figure height
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    # plot grid points, coloured by coverage
    sc = ax.scatter(grid_x,
                    grid_y,
                    c=max_cell_cov,
                    alpha=alpha,
                    vmax=vmax,
                    vmin=vmin,
                    s=64)

    # add basemap
    ctx.add_basemap(ax,
                    url="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
                    crs=crs)

    # add markers at sensor locations
    ax.scatter(sensors[:,0], sensors[:,1],
               edgecolor='blue',
               facecolor='blue',
               s=32,
               marker='x')

    # format axes and titles
    ax.set_title(title, fontsize=24)
    ax.set_axis_off()
    plt.colorbar(sc, cax=cax)
    
    if save_path:
        plt.savefig(save_path, dpi=300)
    
    return fig, ax
