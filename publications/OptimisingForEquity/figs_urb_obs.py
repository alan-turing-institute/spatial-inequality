from pathlib import Path
from typing import Optional
from utils import get_la_save_dir

import contextily as ctx
import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spineq.plotting import (
    get_fig_grid,
    add_colorbar,
    save_fig,
    add_scalebar,
    plot_coverage_grid,
    plot_sensors,
    plot_optimisation_result,
)
from spineq.urb_obs import plot_uo_coverage_grid, get_uo_sensor_dict
from spineq.data_fetcher import lad20nm_to_lad20cd, get_oa_shapes
from spineq.utils import coverage_grid
from spineq.optimise import calc_coverage

from utils import (
    get_config,
    set_fig_style,
    load_pickle,
    get_objectives,
    get_default_optimisation_params,
    get_figures_save_dir,
)
from figs_demographics import get_weights
from networks_single_obj import get_single_obj_filepath


def load_uo_sensors(config: Optional[dict]) -> gpd.GeoDataFrame:
    """Load previously saved Urban Observatory sensor locations.

    Parameters
    ----------
    config : Optional[dict]
        Config dict specifying file path to saved results, as loaded by
        utils.get_config, or if None call utils.get_config directly

    Returns
    -------
    gpd.GeoDataFrame
        Urban Observatory sensor locations
    """
    if config is None:
        config = get_config()
    uo_dir = config["urb_obs"]["save_dir"]
    filename = config["urb_obs"]["filename"]
    la_dir = get_la_save_dir(config)
    uo_path = Path(la_dir, uo_dir, filename)
    return gpd.read_file(uo_path)


def get_uo_coverage_oa(
    lad20cd: str,
    uo_sensor_dict: Optional[list],
    theta: float,
    all_groups: dict,
    oa_weights: dict,
) -> dict:
    """Calculate the coverage of each output area provide by the Urban Observatory
    sensors

    Parameters
    ----------
    lad20cd : str
        Local authority code
    uo_sensor_dict : Optional[list]
        List of dictionaries with the location of each Urban Observatoy sensor, or None
        in which cases this is generated from the output of load_uo_sensors
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective to plot
    oa_weights : dict
        Weight for each output area for each group/objective

    Returns
    -------
    dict
        Coverage of each output area with the Urban Observatory network
    """
    if uo_sensor_dict is None:
        uo_sensors = load_uo_sensors(None)
        uo_sensor_dict = get_uo_sensor_dict(lad20cd, uo_sensors=uo_sensors)

    uo_coverage = {}
    for name, _ in all_groups.items():
        if name == "workplace" and "workplace" not in oa_weights.keys():
            oaw = oa_weights["workers"]
        else:
            oaw = oa_weights[name]
        uo_coverage[name] = calc_coverage(
            lad20cd, uo_sensor_dict, oa_weight=oaw, theta=theta
        )
        uo_coverage[name]["sensors"] = uo_sensor_dict
        uo_coverage[name]["lad20cd"] = lad20cd
    uo_coverage["n_sensors"] = len(uo_sensor_dict)
    return uo_coverage


def get_diff_cmap() -> matplotlib.colors.LinearSegmentedColormap:
    """Creates a purple-white-orange colour map to use when visualising the difference
    in coverage between two networks.

    Returns
    -------
    matplotlib.colors.LinearSegmentedColormap
        Purple-white-orange colour map
    """
    return matplotlib.colors.LinearSegmentedColormap.from_list(
        "", ["purple", "white", "orange"]
    )


def fig_uo_sensor_locations(lad20cd: str, uo_sensors: gpd.GeoDataFrame, save_dir: Path):
    """Show the location of all sensors in the Urban Observatory network (points only).
    Figure nane: urb_obs_sensors_nsensors_{N}.png (where {N} is the no. sensors in the
    UO network)

    Parameters
    ----------
    lad20cd : str
        Local authority code
    uo_sensors : gpd.GeoDataFrame
        Urban Observatory sensor locations
    save_dir : Path
        Directory to save figure
    """
    fig, ax = plt.subplots(1, 1, figsize=(15, 15))
    plot_sensors(lad20cd, uo_sensors, centroids=False, ax=ax)
    add_scalebar(ax)
    save_fig(fig, f"urb_obs_sensors_nsensors_{len(uo_sensors)}.png", save_dir)


def fig_uo_coverage_grid(
    lad20cd: str, uo_sensors: gpd.GeoDataFrame, theta: int, save_dir: Path
):
    """Calculate the coverage the Urban Observatory sensor network provides on a square
    grid. Figure name: urb_obs_coverage_grid_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    lad20cd : str
        Local authority code
    uo_sensors : gpd.GeoDataFrame
        Urban Observatory sensor locations
    theta : int
        Coverage distance to use
    save_dir : Path
        Directory to save figure
    """
    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    ax = ax[0]
    cmap = "Greens"
    plot_uo_coverage_grid(
        lad20cd, uo_sensors=uo_sensors, ax=ax, legend=False, cmap=cmap
    )
    add_colorbar(ax, cmap=cmap, label="Coverage")
    add_scalebar(ax)
    t_str = f"theta_{theta}"
    n_str = f"nsensors_{len(uo_sensors)}"
    save_fig(fig, f"urb_obs_coverage_grid_{t_str}_{n_str}.png", save_dir)


def fig_uo_coverage_grid_diff(
    lad20cd: str,
    uo_sensors: gpd.GeoDataFrame,
    theta: float,
    all_groups: dict,
    networks: dict,
    save_dir: Path,
):
    """Show the coverage difference, on a square grid, between the Urban Observatory
    network and networks optimised for the coverage of single objectives (single
    population sub-groups). Figure name:
    urb_obs_coverage_difference_grid_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    lad20cd : str
        Local authority code
    uo_sensors : gpd.GeoDataFrame
        Urban Observatory sensor locations
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    networks : dict
        Previous optimisation results (e.g. from
        networks_single_obj.make_single_obj_networks)
    save_dir : Path
        Directory to save figure
    """
    uo_sensors_xy = np.array(
        [uo_sensors["geometry"].x.values, uo_sensors["geometry"].y.values]
    ).T
    oa = get_oa_shapes(lad20cd)
    bounds = oa["geometry"].bounds
    xlim = (bounds["minx"].min(), bounds["maxx"].max())
    ylim = (bounds["miny"].min(), bounds["maxy"].max())
    grid_size = 100
    uo_cov = coverage_grid(uo_sensors_xy, xlim, ylim, theta=theta, grid_size=grid_size)

    n_uo_oa = uo_sensors["oa11cd"].nunique()

    fig, grid = get_fig_grid()
    cmap = get_diff_cmap()
    vmin = -1
    vmax = 1
    for i, (name, params) in enumerate(all_groups.items()):
        greedy_sensors = pd.DataFrame(
            networks[name][f"theta{theta}"][f"{n_uo_oa}sensors"]["sensors"]
        )
        greedy_sensors = np.array(greedy_sensors[["x", "y"]])
        greedy_cov = coverage_grid(
            greedy_sensors, xlim, ylim, theta=theta, grid_size=grid_size
        )
        cov_diff = uo_cov.copy()
        cov_diff["coverage"] = greedy_cov["coverage"] - uo_cov["coverage"]

        plot_coverage_grid(
            lad20cd,
            cov_diff,
            ax=grid[i],
            vmin=vmin,
            vmax=vmax,
            legend=False,
            cmap=cmap,
            title=params["title"],
        )
    add_scalebar(grid[1])
    add_colorbar(grid[-1], cmap=cmap, vmin=vmin, vmax=vmax, label="Coverage Difference")

    fig.suptitle(
        f"Comparisons with Urban Observatory Network (n = {n_uo_oa}, $\\theta$ = {theta} m)",
        y=0.87,
        fontsize=20,
    )
    t_str = f"theta_{theta}"
    n_str = f"nsensors_{n_uo_oa}"
    save_fig(fig, f"urb_obs_coverage_difference_grid_{t_str}_{n_str}.png", save_dir)


def fig_uo_coverage_oa(
    uo_coverage: dict, theta: float, all_groups: dict, save_dir: Path
):
    """Plot the coverage of each output area provide by the Urban Observatory
    sensors. Figure name: urb_obs_coverage_oa_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    uo_coverage : dict
        Coverage of each output area with the Urban Observatory network (e.g. from
        get_uo_coverage_oa)
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    save_dir : Path
        Directory to save figure
    """
    title = f"Urban Observatory: Coverage with $\\theta$ = {theta} m\n"
    for name, params in all_groups.items():
        title += f"{params['title']}: {uo_coverage[name]['total_coverage']:.2f}, "
    title = title[:-2]

    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    plot_optimisation_result(
        uo_coverage[name],
        title=title,
        ax=ax[0],
        show=False,
        legend=False,
        sensor_size=50,
        sensor_color="green",
        sensor_edgecolor="yellow",
        sensor_linewidth=1.5,
    )
    add_scalebar(ax[0])
    add_colorbar(ax[0], cmap="Greens", label="Coverage")

    t_str = f"theta_{theta}"
    n_str = f"nsensors_{uo_coverage['n_sensors']}"
    save_fig(fig, f"urb_obs_coverage_oa_{t_str}_{n_str}.png", save_dir)


def fig_uo_coverage_oa_diff(
    lad20cd: str,
    uo_coverage: dict,
    theta: float,
    all_groups: dict,
    networks: dict,
    save_dir: Path,
):
    """Show the coverage difference of each outupt area between the Urban Observatory
    network and networks optimised for the coverage of single objectives (single
    population sub-groups). Figure name:
    urb_obs_coverage_difference_oa_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    lad20cd : str
        Local authority code
    uo_sensors : gpd.GeoDataFrame
        Urban Observatory sensor locations
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    networks : dict
        Previous optimisation results (e.g. from
        networks_single_obj.make_single_obj_networks)
    save_dir : Path
        Directory to save figure
    """
    fig, grid = get_fig_grid()
    cmap = get_diff_cmap()
    n_uo_oa = uo_coverage["n_sensors"]

    for i, (name, params) in enumerate(all_groups.items()):
        uo_cov = uo_coverage[name]["oa_coverage"]
        uo_cov = pd.DataFrame(uo_cov).set_index("oa11cd")
        uo_cov.rename(columns={"coverage": "urb_obs"}, inplace=True)

        greedy_cov = networks[name][f"theta{theta}"][f"{n_uo_oa}sensors"]["oa_coverage"]
        greedy_cov = pd.DataFrame(greedy_cov).set_index("oa11cd")
        greedy_cov.rename(columns={"coverage": "greedy"}, inplace=True)

        compare_nets = uo_cov.join(greedy_cov)
        compare_nets["diff"] = compare_nets["greedy"] - compare_nets["urb_obs"]
        compare_nets["diff"].describe()

        oa_shapes = get_oa_shapes(lad20cd)
        oa_shapes = oa_shapes.join(compare_nets["diff"])

        vmin = -1
        vmax = 1
        oa_shapes.plot(
            column="diff", alpha=0.85, cmap=cmap, ax=grid[i], vmin=vmin, vmax=vmax
        )

        ctx.add_basemap(
            grid[i],
            source="http://a.tile.stamen.com/toner/{z}/{x}/{y}.png",
            crs=oa_shapes.crs.to_epsg(),
        )

        grid[i].set_axis_off()
        grid[i].set_title(params["title"])

    add_scalebar(grid[1])
    add_colorbar(grid[-1], cmap=cmap, label="Coverage Difference", vmin=vmin, vmax=vmax)
    fig.suptitle(
        f"Comparisons with Urban Observatory Network (n = {n_uo_oa}, $\\theta$ = {theta} m)",
        y=0.87,
        fontsize=20,
    )

    t_str = f"theta_{theta}"
    n_str = f"nsensors_{n_uo_oa}"
    save_fig(fig, f"urb_obs_coverage_difference_oa_{t_str}_{n_str}.png", save_dir)


def main():
    """Save figures showing the pre-existing Urban Observatory network of sensors and
    comparisons with optimised networks using our approach.
    """
    print("Saving Urban Observatory figures...")
    set_fig_style()

    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_path = get_single_obj_filepath(config)
    networks = load_pickle(networks_path)
    uo_sensors = load_uo_sensors(config)

    figs_dir = get_figures_save_dir(config)

    population_groups, all_groups = get_objectives(config)
    oa_weights = get_weights(lad20cd, population_groups)
    theta, _ = get_default_optimisation_params(config)

    uo_sensor_dict = get_uo_sensor_dict(lad20cd, uo_sensors=uo_sensors)
    uo_coverage = get_uo_coverage_oa(
        lad20cd, uo_sensor_dict, theta, all_groups, oa_weights
    )

    fig_uo_sensor_locations(lad20cd, uo_sensors, figs_dir)
    fig_uo_coverage_grid(lad20cd, uo_sensors, theta, figs_dir)
    fig_uo_coverage_grid_diff(
        lad20cd, uo_sensors, theta, all_groups, networks, figs_dir
    )
    fig_uo_coverage_oa(uo_coverage, theta, all_groups, figs_dir)
    fig_uo_coverage_oa_diff(lad20cd, uo_coverage, theta, all_groups, networks, figs_dir)


if __name__ == "__main__":
    main()
