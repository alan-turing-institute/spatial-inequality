from pathlib import Path
from typing import Dict, Optional

import contextily as ctx
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from networks_single_obj import get_single_obj_filepath
from utils import (
    add_subplot_label,
    get_config,
    get_default_optimisation_params,
    get_figures_params,
    get_la,
    get_la_save_dir,
    get_objectives,
    load_jsonpickle,
    set_fig_style,
)

from spineq.data.group import LocalAuthority
from spineq.data.urb_obs import UODataset
from spineq.mappings import lad20nm_to_lad20cd
from spineq.opt.coverage import ExponentialCoverage
from spineq.opt.objectives import Column, CombinedObjectives
from spineq.opt.result import SingleNetworkResult
from spineq.plot.plotting import (
    add_colorbar,
    add_scalebar,
    get_fig_grid,
    plot_coverage_grid,
    plot_optimisation_result,
    plot_sensors,
    save_fig,
)
from spineq.urb_obs import plot_uo_coverage_grid
from spineq.utils import coverage_grid


def load_uo_sensors(config: Optional[dict]) -> UODataset:
    """Load previously saved Urban Observatory sensor locations.

    Parameters
    ----------
    config : Optional[dict]
        Config dict specifying file path to saved results, as loaded by
        utils.get_config, or if None call utils.get_config directly

    Returns
    -------
    UODataset
        Urban Observatory sensor locations
    """
    if config is None:
        config = get_config()
    uo_dir = config["urb_obs"]["save_dir"]
    filename = config["urb_obs"]["filename"]
    la_dir = get_la_save_dir(config)
    uo_path = Path(la_dir, uo_dir, filename)
    return UODataset.read_jsonpickle(uo_path)


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


def fig_uo_sensor_locations(
    la: LocalAuthority, uo_sensors: UODataset, save_dir: Path, extension: str
):
    """Show the location of all sensors in the Urban Observatory network (points only).
    Figure nane: urb_obs_sensors_nsensors_{N}.png (where {N} is the no. sensors in the
    UO network)

    Parameters
    ----------
    la : LocalAuthority
        Local authority
    uo_sensors : UODataset
        Urban Observatory sensor locations
    save_dir : Path
        Directory to save figure
    extension : str
        Figure file format
    """
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))
    plot_sensors(la, uo_sensors, centroids=False, ax=ax)
    add_scalebar(ax)
    save_fig(fig, f"urb_obs_sensors_nsensors_{len(uo_sensors)}", save_dir, extension)


def fig_uo_coverage_grid(
    la: LocalAuthority,
    uo_sensors: UODataset,
    theta: int,
    save_dir: Path,
    extension: str,
):
    """Calculate the coverage the Urban Observatory sensor network provides on a square
    grid. Figure name: urb_obs_coverage_grid_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    la : LocalAuthority
        Local authority
    uo_sensors : UODataset
        Urban Observatory sensor locations
    theta : int
        Coverage distance to use
    save_dir : Path
        Directory to save figure
    extension : str
        Figure file format
    """
    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    ax = ax[0]
    cmap = "Greens"
    plot_uo_coverage_grid(la, uo_sensors=uo_sensors, ax=ax, legend=False, cmap=cmap)
    add_colorbar(ax, cmap=cmap, label="Coverage")
    add_scalebar(ax)
    t_str = f"theta_{theta}"
    n_str = f"nsensors_{len(uo_sensors)}"
    save_fig(fig, f"urb_obs_coverage_grid_{t_str}_{n_str}", save_dir, extension)


def fig_uo_coverage_grid_diff(
    la: str,
    uo_sensors: UODataset,
    theta: float,
    all_groups: dict,
    networks: dict,
    save_dir: Path,
    extension: str,
):
    """Show the coverage difference, on a square grid, between the Urban Observatory
    network and networks optimised for the coverage of single objectives (single
    population sub-groups). Figure name:
    urb_obs_coverage_difference_grid_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    la : LocalAuthority
        Local authority
    uo_sensors : UODataset
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
    extension : str
        Figure file format
    """
    uo_sensors_xy = np.array(
        [uo_sensors.values["geometry"].x.values, uo_sensors.values["geometry"].y.values]
    ).T
    oa = la.oa_shapes.values
    bounds = oa["geometry"].bounds
    xlim = (bounds["minx"].min(), bounds["maxx"].max())
    ylim = (bounds["miny"].min(), bounds["maxy"].max())
    grid_size = 100
    uo_cov = coverage_grid(uo_sensors_xy, xlim, ylim, theta=theta, grid_size=grid_size)

    n_uo_oa = uo_sensors.values["oa11cd"].nunique()

    fig, grid = get_fig_grid()
    cmap = get_diff_cmap()
    vmin = -1
    vmax = 1
    for i, (name, params) in enumerate(all_groups.items()):
        greedy_result = networks[name][f"theta{theta}"][f"{n_uo_oa}sensors"]["sensors"]
        greedy_xy = np.array(
            la.oa_centroids.values[["x", "y"]].iloc[greedy_result.placement_history, :]
        )
        greedy_cov = coverage_grid(
            greedy_xy, xlim, ylim, theta=theta, grid_size=grid_size
        )
        cov_diff = uo_cov.copy()
        cov_diff["coverage"] = greedy_cov["coverage"] - uo_cov["coverage"]

        plot_coverage_grid(
            la,
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
        (
            f"Comparisons with Urban Observatory Network "
            f"(n = {n_uo_oa}, $\\theta$ = {theta} m)"
        ),
        y=0.89,
        fontsize=12,
    )
    t_str = f"theta_{theta}"
    n_str = f"nsensors_{n_uo_oa}"
    save_fig(
        fig, f"urb_obs_coverage_difference_grid_{t_str}_{n_str}", save_dir, extension
    )


def get_uo_coverage_results_oa(
    la: LocalAuthority, uo_sensors: UODataset, theta: float, all_groups: dict
) -> Dict[SingleNetworkResult]:
    """Compute Urban Observatory sensor network coverage

    Parameters
    ----------
    la : LocalAuthority
        Local Authority object with all datasets in all_groups added
    uo_sensors : UODataset
        Urban Observatory sensor locations
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective

    Returns
    -------
    Dict[SingleNetworkResult]
        Urban Observatory sensor network coverage for each objective
    """
    results = {}
    cov = ExponentialCoverage.from_la(la, theta)
    for name in all_groups:
        objs = CombinedObjectives(la, [Column(name, "total")], cov)
        sensors = objs.names_to_sensors(uo_sensors.values["oa11cd"].unique())
        total_coverage = objs.fitness(sensors)
        results[name] = SingleNetworkResult(
            objs, len(uo_sensors.values), sensors, total_coverage
        )
    return results


def fig_uo_coverage_oa(
    la: LocalAuthority,
    uo_sensors: UODataset,
    theta: float,
    all_groups: dict,
    save_dir: Path,
    extension: str,
):
    """Plot the coverage of each output area provide by the Urban Observatory
    sensors. Figure name: urb_obs_coverage_oa_theta_{theta}_nsensors_{n_sensors}.png

    Parameters
    ----------
    la : LocalAuthority
        Local Authority object with all datasets in all_groups added
    uo_sensors : UODataset
        Urban Observatory sensor locations
    theta : float
        Coverage distance to use
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    save_dir : Path
        Directory to save figure
    """
    results = get_uo_coverage_results_oa(la, uo_sensors, theta, all_groups)
    title = f"Urban Observatory: Coverage with $\\theta$ = {theta} m\n"
    for name, params in all_groups.items():
        title += f"{params['title']}: {results[name].total_coverage:.2f}, "
    title = title[:-2]

    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    plot_optimisation_result(
        results[name],
        title=title,
        ax=ax[0],
        show=False,
        legend=False,
        sensor_size=20,
        sensor_color="green",
        sensor_edgecolor="yellow",
        sensor_linewidth=1,
    )
    add_scalebar(ax[0])
    add_colorbar(ax[0], cmap="Greens", label="Coverage")

    t_str = f"theta_{theta}"
    n_str = f"nsensors_{results[name].n_sensors}"
    save_fig(fig, f"urb_obs_coverage_oa_{t_str}_{n_str}", save_dir, extension)


def fig_uo_coverage_oa_diff(
    la: LocalAuthority,
    uo_sensors: UODataset,
    theta: float,
    all_groups: dict,
    networks: dict,
    save_dir: Path,
    extension: str,
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
    extension : str
        Figure file format
    """
    fig, grid = get_fig_grid()
    cmap = get_diff_cmap()
    uo_results = get_uo_coverage_results_oa(la, uo_sensors, theta, all_groups)

    for i, (name, params) in enumerate(all_groups.items()):
        n_uo_oa = uo_results[name].n_sensors
        uo_cov = uo_results[name].objectives.oa_coverage(uo_results[name].sensors)
        uo_cov = pd.DataFrame({"urb_obs": uo_cov}, index=la.oa11cd)

        greedy_cov = networks[name][f"theta{theta}"][
            f"{n_uo_oa}sensors"
        ].objectives.oa_coverage(
            networks[name][f"theta{theta}"][f"{n_uo_oa}sensors"].sensors
        )
        greedy_cov = pd.DataFrame({"greedy": greedy_cov}, index=la.oa11cd)

        compare_nets = uo_cov.join(greedy_cov)
        compare_nets["diff"] = compare_nets["greedy"] - compare_nets["urb_obs"]
        compare_nets["diff"].describe()

        oa_shapes = la.oa_shapes
        oa_shapes = oa_shapes.values.join(compare_nets["diff"])

        vmin = -1
        vmax = 1
        oa_shapes.plot(
            column="diff", alpha=0.85, cmap=cmap, ax=grid[i], vmin=vmin, vmax=vmax
        )

        ctx.add_basemap(
            grid[i],
            source=ctx.providers.Stamen.TonerBackground,
            crs=oa_shapes.crs.to_epsg(),
            attribution_size=5,
            attribution="",
        )

        grid[i].set_axis_off()
        grid[i].set_title(params["title"])
        add_subplot_label(fig, grid[i], i, xt=0, yt=22 / 72)

    add_scalebar(grid[1])
    add_colorbar(grid[-1], cmap=cmap, label="Coverage Difference", vmin=vmin, vmax=vmax)
    fig.suptitle(
        (
            f"Comparisons with Urban Observatory Network "
            f"(n = {n_uo_oa}, $\\theta$ = {theta} m)"
        ),
        y=0.89,
        fontsize=12,
    )

    t_str = f"theta_{theta}"
    n_str = f"nsensors_{n_uo_oa}"
    save_fig(
        fig, f"urb_obs_coverage_difference_oa_{t_str}_{n_str}", save_dir, extension
    )


def main():
    """Save figures showing the pre-existing Urban Observatory network of sensors and
    comparisons with optimised networks using our approach.
    """
    print("Saving Urban Observatory figures...")
    set_fig_style()

    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    population_groups, all_groups = get_objectives(config)
    la = get_la(lad20cd, population_groups)
    networks_path = get_single_obj_filepath(config)
    networks = load_jsonpickle(networks_path)
    uo_sensors = load_uo_sensors(config)

    figs_dir, extension = get_figures_params(config)

    theta, _ = get_default_optimisation_params(config)

    fig_uo_sensor_locations(la, uo_sensors, figs_dir, extension)
    fig_uo_coverage_grid(la, uo_sensors, theta, figs_dir, extension)
    fig_uo_coverage_grid_diff(
        la, uo_sensors, theta, all_groups, networks, figs_dir, extension
    )
    fig_uo_coverage_oa(la, uo_sensors, theta, all_groups, figs_dir, extension)
    fig_uo_coverage_oa_diff(
        la, uo_sensors, theta, all_groups, networks, figs_dir, extension
    )


if __name__ == "__main__":
    main()
