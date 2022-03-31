"""Functions for visualising the data, optimisation weights and
optimisation results.
"""
from pathlib import Path
from typing import Union

import contextily as ctx
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib_scalebar.scalebar import ScaleBar
from mpl_toolkits.axes_grid1 import ImageGrid, make_axes_locatable

from spineq.data_fetcher import get_oa_centroids, get_oa_shapes
from spineq.utils import coverage_matrix


def get_color_axis(ax):
    """Make a colour axis matched to be the same size as the plot.
    See: https://www.science-emergence.com/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
    """
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    return cax


def plot_optimisation_result(
    result,
    title=None,
    save_path=None,
    ax=None,
    figsize=(10, 10),
    fill_oa=True,
    cmap="YlGn",
    legend=True,
    alpha=0.75,
    sensor_size=36,
    sensor_color="darkgreen",
    sensor_edgecolor="white",
    sensor_linewidth=1.5,
    fontsize=20,
    show=True,
    vmin=0,
    vmax=1,
    basemap=ctx.providers.Stamen.TonerBackground,
):
    """
    Plot map with sensor locations (red points), output area centroids (black points),
    and coverage (shaded areas).
    """
    sensors = pd.DataFrame(result["sensors"])
    sensors.set_index("oa11cd", inplace=True)

    oa_coverage = pd.DataFrame(result["oa_coverage"])
    oa_coverage.set_index("oa11cd", inplace=True)

    oa_shapes = get_oa_shapes(result["lad20cd"])

    oa_shapes["coverage"] = oa_coverage

    if ax is None:
        ax = plt.figure(figsize=figsize).gca()

    # to make colorbar same size as graph:
    # https://www.science-emergence.com/Articles/How-to-match-the-colorbar-size-with-the-figure-size-in-matpltolib-/
    if legend and fill_oa:
        cax = get_color_axis(ax)
        cax.set_title("Coverage")
    else:
        cax = None

    if fill_oa:
        ax = oa_shapes.plot(
            column="coverage",
            alpha=alpha,
            cmap=cmap,
            legend=legend,
            ax=ax,
            cax=cax,
            vmin=vmin,
            vmax=vmax,
        )
    else:
        ax = oa_shapes.plot(
            alpha=alpha, ax=ax, facecolor="none", edgecolor="none", linewidth=0.5
        )

    ax.scatter(
        sensors["x"],
        sensors["y"],
        s=sensor_size,
        color=sensor_color,
        edgecolor=sensor_edgecolor,
        linewidth=sensor_linewidth,
    )

    if basemap:
        ctx.add_basemap(
            ax,
            source=basemap,
            crs=oa_shapes.crs.to_epsg(),
            attribution_size=5,
            attribution="",
        )

    ax.set_axis_off()
    if title is None:
        ax.set_title(
            "n_sensors = {:.0f}, coverage = {:.2f}".format(
                len(sensors), result["total_coverage"]
            ),
            fontsize=fontsize,
        )
    else:
        ax.set_title(title)

    if save_path:
        plt.tight_layout()
        plt.savefig(save_path, dpi=200)
        plt.close()
    elif show:
        plt.show()


def plot_coverage_grid(
    lad20cd,
    grid_cov,
    crs={"init": "epsg:27700"},
    threshold=0.005,
    alpha=0.75,
    ax=None,
    legend=True,
    title="",
    figsize=(15, 15),
    vmin=0,
    vmax=1,
    save_path=None,
    cmap="viridis",
    basemap=ctx.providers.Stamen.TonerBackground,
):
    """Generate a square grid of points and show them on a map coloured by
    coverage due to the closest sensor to each grid point.

    Arguments:
        grid_cov {GeoDataFrame} -- Grid squares and coverage as calculated by
        utils.coverage_grid.

    Keyword Arguments:
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
    if ax is None:
        ax = plt.figure(figsize=figsize).gca()

    if legend:
        cax = get_color_axis(ax)
        cax.set_title("Coverage")
    else:
        cax = None

    oa_shapes = get_oa_shapes(lad20cd)
    oa_shapes.plot(ax=ax, edgecolor="k", facecolor="None")
    grid_cov.plot(
        column="coverage",
        cmap=cmap,
        alpha=[alpha if abs(c) > threshold else 0 for c in grid_cov["coverage"]],
        ax=ax,
        vmin=vmin,
        vmax=vmax,
        cax=cax,
        legend=legend,
    )
    if basemap:
        ctx.add_basemap(
            ax,
            source=basemap,
            crs=crs,
            attribution_size=5,
            attribution="",
        )
    ax.set_axis_off()
    ax.set_title(title, fontsize=20)

    if save_path:
        plt.savefig(save_path, dpi=200)
        plt.close()

    return ax


def plot_oa_weights(
    lad20cd,
    oa_weights,
    title="",
    save_path=None,
    ax=None,
    figsize=(10, 10),
    alpha=0.75,
    cmap="plasma",
    legend=True,
    show=True,
    vmin=0,
    vmax=1,
    basemap=ctx.providers.Stamen.TonerBackground,
):
    # YlGnBu
    oa_shapes = get_oa_shapes(lad20cd)
    oa_shapes["weight"] = oa_weights

    if ax is None:
        ax = plt.figure(figsize=figsize).gca()

    if legend:
        cax = get_color_axis(ax)
    else:
        cax = None

    ax = oa_shapes.plot(
        column="weight",
        figsize=figsize,
        alpha=alpha,
        cmap=cmap,
        legend=legend,
        ax=ax,
        cax=cax,
        vmin=vmin,
        vmax=vmax,
    )

    if basemap:
        ctx.add_basemap(
            ax,
            source=basemap,
            crs=oa_shapes.crs.to_epsg(),
            attribution_size=5,
            attribution="",
        )
    ax.set_title(title)
    ax.set_axis_off()

    if save_path:
        plt.savefig(save_path, dpi=200)
        plt.close()
    elif show:
        plt.show()


def plot_oa_importance(
    lad20cd,
    oa_weights,
    theta=500,
    title="",
    save_path=None,
    ax=None,
    figsize=(10, 10),
    alpha=0.75,
    cmap="plasma",
    legend=True,
    vmin=None,
    vmax=None,
    show=True,
    basemap=ctx.providers.Stamen.TonerBackground,
):
    """Plot the "importance" of each OA given a weighting for each
    OA and a coverage distance (theta). Importance is defined as the
    total coverage (of the city) by placing a sensor at the OA centroid.
    With the greedy optimisation algorithm, the OA with the highest
    importance is where the first sensor in the network will be placed.

    Arguments:
        oa_weights {pd.Series} -- Weights for each OA (indexed by oa11cd)

    Keyword Arguments:
        theta {int} -- coverage decay rate (default: {500})
        title {str} -- plot title (default: {""})
        save_path {str} -- path to save output plot or None to not save
        (default: {None})
        ax {[type]} -- matplotlib qxis to plot to (create one if None)
        figsize {tuple} -- plot figure size (default: {(10,10)})
        alpha {float} -- transparency of fill areas (default: {0.75})
        cmap {str} -- matplotlib colormap for fill areas (default: {"plasma"})
        legend {bool} -- if True show the color scale (default: {True})
        vmin {[type]} -- minimum value of color scale, or None to autoscale (default: {None})
        vmax {[type]} -- maximum value of color scale, or None to autoscale (default: {None})
    """

    oa_centroids = get_oa_centroids(lad20cd)
    oa_centroids["weight"] = oa_weights

    oa_x = oa_centroids["x"].values
    oa_y = oa_centroids["y"].values
    oa_weight = oa_centroids["weight"].values
    oa11cd = oa_centroids.index.values

    n_poi = len(oa_x)
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    # to store total coverage due to a sensor at any output area
    oa_importance = np.zeros(n_poi)

    for site in range(n_poi):
        oa_importance[site] = (oa_weight * coverage[site, :]).sum() / oa_weight.sum()

    oa_importance = pd.Series(data=oa_importance, index=oa11cd)

    oa_shapes = get_oa_shapes(lad20cd)
    oa_shapes["importance"] = oa_importance

    if ax is None:
        ax = plt.figure(figsize=figsize).gca()

    if legend:
        cax = get_color_axis(ax)
        cax.set_title("Density")

    else:
        cax = None

    ax = oa_shapes.plot(
        column="importance",
        figsize=figsize,
        alpha=alpha,
        cmap=cmap,
        legend=legend,
        ax=ax,
        cax=cax,
        vmin=vmin,
        vmax=vmax,
    )

    if basemap:
        ctx.add_basemap(
            ax,
            source=basemap,
            crs=oa_shapes.crs.to_epsg(),
            attribution_size=5,
            attribution="",
        )
    ax.set_title(title)
    ax.set_axis_off()

    if save_path:
        plt.savefig(save_path, dpi=200)
        plt.close()
    elif show:
        plt.show()


def plot_sensors(
    lad20cd,
    sensors,
    shapes=True,
    centroids=True,
    title="",
    ax=None,
    basemap=ctx.providers.Stamen.TonerBackground,
):
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(7, 7))

    if shapes:
        oa = get_oa_shapes(lad20cd)
        oa.plot(linewidth=1, ax=ax, facecolor="yellow", edgecolor="blue", alpha=0.1)

    if centroids:
        c = get_oa_centroids(lad20cd)
        ax.scatter(c["x"], c["y"], s=5)

    sensors.plot(ax=ax, edgecolor="yellow", facecolor="red", markersize=35, linewidth=1)
    if basemap:
        ctx.add_basemap(
            ax,
            source=basemap,
            crs=sensors.crs,
            attribution_size=5,
            attribution="",
        )
    ax.set_axis_off()
    ax.set_title(title)


def get_fig_grid(figsize=(7, 7), nrows_ncols=(2, 2)):
    fig = plt.figure(figsize=figsize)
    grid = ImageGrid(
        fig,
        111,
        nrows_ncols=nrows_ncols,
        axes_pad=0.35,
        share_all=True,
        cbar_location="right",
        cbar_mode="single",
        cbar_size="4%",
        cbar_pad=0.35,
    )

    return fig, grid


def add_colorbar(ax, vmin=0, vmax=1, cmap="plasma", label=""):
    ax.cax.colorbar(
        mpl.cm.ScalarMappable(
            norm=mpl.colors.Normalize(vmin=vmin, vmax=vmax), cmap=cmap
        ),
        label=label,
    )


def add_scalebar(ax):
    ax.add_artist(ScaleBar(1))


def save_fig(fig, filename, save_dir, extension=".png", dpi=600, bbox_inches="tight"):
    fig.savefig(
        Path(save_dir, f"{filename}{extension}"), dpi=dpi, bbox_inches=bbox_inches
    )


def networks_swarmplot(
    scores: np.ndarray,
    objectives: list,
    thresholds: Union[float, dict, None] = None,
    colors: list = ("pink", "blue", "orange"),
    ax: Union[plt.Axes, None] = None,
    highlight: Union[int, list, None] = None,
    legend: bool = False,
) -> plt.Axes:
    """Create a swarrmplot showing the coverage values for each individual objective
    for all networks in a population of multi-objective optimisation results.

    Parameters
    ----------
    scores : np.ndarray
        Coverage scores for each objective in each network
        (shape: n_networks, n_objectives)
    objectives : list
        Name of each objective
    thresholds : Union[float, dict, None], optional
        Optionally apply a selection threshold to each objective. Either a float which
        applies the same threshold to all objectives, or a dict of objective: threshold
        pairs. By default None
    colors : list, optional
        Colours to use to show networks that don't an do exceed the set thresholds,
        by default ["pink", "blue"]
    ax : plt.Axes, optional
        Matplotlib axis to plot to, by default None
    highlight : Union[int, list, None], optional
        Index or indices of individual networks to highlight, by default None
    legend : bool, optional
        If True display a legend, by default False

    Returns
    -------
    plt.Axes
        Matplotlib axis with swarm plot.
    """
    df = pd.DataFrame(scores, columns=objectives)

    selected = None
    if isinstance(thresholds, float):
        selected = df[objectives[0]] > thresholds
        for obj in objectives[1:]:
            selected = selected & (df[obj] > thresholds)

    elif isinstance(thresholds, dict):
        for obj, t in thresholds.items():
            selected = df[obj] > t if selected is None else selected & (df[obj] > t)

    if highlight is not None:
        if selected is not None:
            selected = selected.astype(int).values
        else:
            selected = np.zeros(len(df))
        if isinstance(highlight, int):
            highlight = [highlight]
        for class_label, idx in enumerate(highlight, start=int(selected.max()) + 1):
            selected[idx] = class_label
        selected = pd.Series(selected)

    df = df[objectives].stack()
    df.name = "coverage"
    df.index.set_names(["idx", "objective"], inplace=True)
    df = pd.DataFrame(df)

    if selected is not None:
        selected.name = "selected"
        selected.index.name = "idx"
        df = pd.merge(df, selected, how="left", left_index=True, right_index=True)

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(10, 5))

    if selected is not None:
        sns.swarmplot(
            x="objective",
            y="coverage",
            hue="selected",
            palette=sns.color_palette(colors),
            data=df.reset_index(),
            size=4,
            ax=ax,
        )
        ax.get_legend().remove()

    else:
        sns.swarmplot(
            x="objective",
            y="coverage",
            data=df.reset_index(),
            size=4,
            ax=ax,
            palette=sns.color_palette(colors),
        )

    ax.set_xlabel("")
    if isinstance(thresholds, float):
        ax.axhline(thresholds, color="k", linewidth=0.5)
    elif isinstance(thresholds, dict):
        for i, obj in enumerate(objectives):
            if obj in thresholds.keys():
                ax.hlines(thresholds[obj], i - 0.35, i + 0.35, color="k", linewidth=0.5)

    if legend:
        ax.legend()

    return ax


def networks_parallel_coords_plot(
    scores: np.ndarray,
    objectives: list,
    thresholds: Union[float, dict, int, None] = None,
    names: Union[str, dict, None] = None,
    colors: list = ("pink", "blue"),
    ax: Union[plt.Axes, None] = None,
) -> plt.Axes:
    """Create a parallel coordinates plot showing the coverage values for each
    individual objective for all networks in a population of multi-objective
    optimisation results.

    Parameters
    ----------
    scores : np.ndarray
        Coverage scores for each objective in each network
        (shape: n_networks, n_objectives)
    objectives : list
        Name of each objective
    thresholds : Union[float, dict, int, None], optional
        Optionally apply a selection threshold to each objective. Either a float which
        applies the same threshold to all objectives, a dict of objective: threshold
        pairs, or an int representing the index of a single network to highlight. By
        default None
    colors : list, optional
        Colours to use to show networks that don't an do exceed the set thresholds,
        by default ["pink", "blue"]
    ax : plt.Axes, optional
        Matplotlib axis to plot to, by default None

    Returns
    -------
    plt.Axes
        Matplotlib axis with parallel coordinates plot.
    """
    df = pd.DataFrame(scores, columns=objectives)

    selected = None
    if isinstance(thresholds, float):
        selected = df[objectives[0]] > thresholds
        for obj in objectives[1:]:
            selected = selected & (df[obj] > thresholds)

    elif isinstance(thresholds, int):
        selected = np.zeros(len(df)).astype(bool)
        selected[thresholds] = True
        selected = pd.Series(selected)

    elif isinstance(thresholds, dict):
        for obj, t in thresholds.items():
            selected = df[obj] > t if selected is None else selected & (df[obj] > t)

    if selected is None:
        df["selected"] = True
    else:
        df["selected"] = selected

    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(10, 5))

    pd.plotting.parallel_coordinates(
        scores,
        "selected",
        color=["pink", "blue"],
        linewidth=1,
        ax=ax,
    )

    ax.set_xlabel("")
    if isinstance(thresholds, float):
        ax.axhline(thresholds, color="k", linewidth=0.5)
    elif isinstance(thresholds, dict):
        # TODO: Ensure objective order of thresholds is same as plot order
        ax.plot(thresholds.values(), "k--")

    return ax
