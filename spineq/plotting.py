import numpy as np
import geopandas as gpd
import pandas as pd

import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import contextily as ctx

from .utils import coverage_matrix
from .data_fetcher import get_data, get_oa_shapes, get_oa_centroids


def get_color_axis(ax):
    """Make a colour axis matched to be the same size as the plot.
    See: https://www.science-emergence.com/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
    """
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    return cax


def plot_optimisation_result(result, title=None, save_path=None,
                             figsize=(10, 10), fill_oa=True,
                             cmap="YlGn", legend=True, alpha=0.75,
                             sensor_size=36, sensor_color='darkgreen',
                             sensor_edgecolor='white', fontsize=20, vmin=0,
                             vmax=1):
    """
    Plot map with sensor locations (red points), output area centroids (black points),
    and coverage (shaded areas).
    """
    
    sensors = pd.DataFrame(result["sensors"])
    sensors.set_index("oa11cd", inplace=True)
    
    oa_coverage = pd.DataFrame(result["oa_coverage"])
    oa_coverage.set_index("oa11cd", inplace=True)
    
    oa_shapes = get_oa_shapes()

    oa_shapes["coverage"] = oa_coverage
    
    # to make colorbar same size as graph:
    # https://www.science-emergence.com/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
    ax = plt.figure(figsize=figsize).gca()
    if legend and fill_oa:
        cax = get_color_axis(ax)
        cax.set_title("Coverage")
    else:
        cax = None

    if fill_oa:
        ax = oa_shapes.plot(column="coverage",
                            alpha=alpha,
                            cmap=cmap, legend=legend,
                            ax=ax, cax=cax, vmin=vmin, vmax=vmax)
    else:
        ax = oa_shapes.plot(alpha=alpha, ax=ax, facecolor='none', edgecolor='k',
                            linewidth=0.5)
    
    ax.scatter(sensors["x"], sensors["y"], s=sensor_size, color=sensor_color,
               edgecolor=sensor_edgecolor)

    ctx.add_basemap(ax,
                    url="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
                    crs=oa_shapes.crs.to_epsg())

    ax.set_axis_off()
    if title is None:
        ax.set_title("n_sensors = {:.0f}, coverage = {:.2f}".format(
                     len(sensors), result["total_coverage"]),
                     fontsize=fontsize)
    else:
        ax.set_title(title)
    
    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=200)
        plt.close()
    else:
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
    grid_cov = coverage_matrix(grid_x,
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
    cax = get_color_axis()
    
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
        plt.savefig(save_path, dpi=200)
        plt.close()
    
    return fig, ax


def plot_oa_weights(oa_weights, title="", save_path=None, figsize=(10,10),
                    alpha=0.75, cmap="plasma", legend=True, vmin=0, vmax=1):
    #YlGnBu
    oa_shapes = get_oa_shapes()
    oa_shapes["weight"] = oa_weights
    
    ax = plt.figure(figsize=figsize).gca()
    
    if legend:
        cax = get_color_axis(ax)
    else:
        cax = None
    
    ax = oa_shapes.plot(column="weight", figsize=figsize, alpha=alpha,
                        cmap=cmap, legend=legend, ax=ax, cax=cax)

    ctx.add_basemap(ax,
                    url="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
                    crs=oa_shapes.crs.to_epsg())
    ax.set_title(title)
    ax.set_axis_off()
    
    if save_path:
        plt.savefig(save_path, dpi=200)
        plt.close()
    else:
        plt.show()


def plot_oa_importance(oa_weights, theta=500,
                       title="", save_path=None, figsize=(10,10),
                       alpha=0.75, cmap="plasma", legend=True, vmin=None,
                       vmax=None):
        
    oa_centroids = get_oa_centroids()
    oa_centroids["weight"] = oa_weights
    
    oa_x = oa_centroids["x"].values
    oa_y = oa_centroids["y"].values
    oa_weight = oa_centroids["weight"].values
    oa11cd = oa_centroids.index.values
        
    n_poi = len(oa_x)
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)
    
    # binary array - 1 if sensor at this location, 0 if not
    sensors = np.zeros(n_poi)

    # to store total coverage due to a sensor at any output area
    oa_importance = np.zeros(n_poi)
        
    for site in range(n_poi):
        # add sensor at poi
        sensors = np.zeros(n_poi)
        sensors[site] = 1

        oa_importance[site] = ((oa_weight * coverage[site, :]).sum()
                                / oa_weight.sum())

    oa_importance = pd.Series(data=oa_importance, index=oa11cd)
    
    oa_shapes = get_oa_shapes()
    oa_shapes["importance"] = oa_importance
    
    ax = plt.figure(figsize=figsize).gca()
    
    if legend:
        cax = get_color_axis(ax)
        cax.set_title("Importance")

    else:
        cax = None
    
    ax = oa_shapes.plot(column="importance", figsize=figsize, alpha=alpha,
                        cmap=cmap, legend=legend, ax=ax, cax=cax, vmin=vmin,
                        vmax=vmax)

    ctx.add_basemap(ax,
                    url="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
                    crs=oa_shapes.crs.to_epsg())
    ax.set_title(title)
    ax.set_axis_off()
    
    if save_path:
        plt.savefig(save_path, dpi=200)
        plt.close()
    else:
        plt.show()
    