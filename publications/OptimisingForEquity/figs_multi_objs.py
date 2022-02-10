from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from figs_urb_obs import get_uo_coverage_oa, load_uo_sensors
from networks_multi_objs import get_multi_obj_inputs, get_multi_objs_filepath
from utils import (
    get_config,
    get_default_optimisation_params,
    get_figures_save_dir,
    get_objectives,
    load_pickle,
    set_fig_style,
)

from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.genetic import extract_all
from spineq.optimise import calc_coverage
from spineq.plotting import (
    add_colorbar,
    add_scalebar,
    get_fig_grid,
    networks_swarmplot,
    plot_optimisation_result,
    save_fig,
)


def fig_all_above_threshold(
    scores: np.ndarray,
    objs: list,
    threshold: float,
    theta: float,
    n_sensors: int,
    save_dir: Path,
):
    """Create a swarm plot of points for each candidate network, highlighting those with
    coverage above a set threshold for all objectives. Figure name:
    multiobj_theta{theta}_{n_sensors}sensors_above{threshold}cov.png

    Parameters
    ----------
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    objs : list
        Names of objectives in the order they appear in scores
    threshold : float
        Highlight networks that have greater than this value of coverage for all
        objectives
    theta : float
        Coverage distance to use
    n_sensors : int
        No. of sensors in the network
    save_dir : Path
        Directory to save figure
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    networks_swarmplot(scores, objs, thresholds=threshold, ax=ax)
    save_fig(
        fig,
        f"multiobj_theta{theta}_{n_sensors}sensors_above{round(threshold * 100)}cov.png",
        save_dir,
    )


def fig_work_above_threshold(
    scores: np.ndarray,
    objs: list,
    threshold: float,
    theta: float,
    n_sensors: int,
    work_name: str,
    save_dir: Path,
):
    """Create a swarm plot of points for each candidate network, highlighting those with
    above a threshold of coverage of workplaces. Figure name:
    multiobj_theta{theta}_{n_sensors}sensors_workabove{threshold}cov.png

    Parameters
    ----------
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    objs : list
        Names of objectives in the order they appear in scores
    threshold : float
        Highlight networks that have greater than this value of coverage for all
        objectives
    theta : float
        Coverage distance to use
    n_sensors : int
        No. of sensors in the network
    work_name : str
        Name of the workplace objective
    save_dir : Path
        Directory to save figure
    """
    work_idx = objs.index(work_name)
    if (scores[:, work_idx] < threshold).all():
        print(f"No networks with workplace coverage > {threshold}, skipping figure")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    networks_swarmplot(scores, objs, thresholds={work_name: threshold}, ax=ax)
    save_fig(
        fig,
        f"multiobj_theta{theta}_{n_sensors}sensors_workabove{round(threshold * 100)}cov.png",
        save_dir,
    )


def fig_max_child_work_above_threshold(
    lad20cd: str,
    scores: np.ndarray,
    objs: list,
    threshold: float,
    theta: float,
    n_sensors: int,
    solutions: np.ndarray,
    inputs: dict,
    work_name: str,
    child_name: str,
    save_dir: Path,
):
    """From a set of candidate networks, plot the one that maximsies coverage of
    children whlist also keeping the coverage of worklplaces above a minimum threshold.
    Figure name:
    multiobj_wplace{work_cov}_child{child_cov}_theta{theta}_{n_sensors}sensors.png

    Parameters
    ----------
    lad20cd : str
        Local authority code
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    objs : list
        Names of objectives in the order they appear in scores
    threshold : float
        Only consider networks with at least this coverage of workplaces
    theta : float
        Coverage distance to use
    n_sensors : int
        No. of sensors in the network
    solutions : np.ndarray
        Sensor output area indices for each candidate network
    inputs : dict
        Optimisation inputs from networks_multi_objs.get_multi_obj_inputs
    work_name : str
        Name of the workplace objective
    child_name : str
        Name of the coverage of children objective
    save_dir : Path
        Directory to save the figure
    """
    work_idx = objs.index(work_name)
    child_idx = objs.index(child_name)
    if (scores[:, work_idx] < threshold).all():
        print(f"No networks with workplace coverage > {threshold}, skipping figure")
        return

    network_idx = scores[scores[:, work_idx] > threshold, child_idx].argmax()
    sensor_idx = solutions[scores[:, work_idx] > threshold][network_idx].astype(int)
    cov = scores[scores[:, work_idx] > threshold][network_idx]

    sensor_dict = [
        {
            "oa11cd": inputs["oa11cd"][idx],
            "x": inputs["oa_x"][idx],
            "y": inputs["oa_y"][idx],
        }
        for idx in sensor_idx
    ]

    # select weight for 1st objective
    # (weights don't matter for calculating coverage of each OA, only for calculating
    # overrall coverage)
    w = list(inputs["oa_weight"].values())[0]
    coverage = calc_coverage(lad20cd, sensor_dict, oa_weight=w, theta=theta)
    coverage["sensors"] = sensor_dict
    coverage["lad20cd"] = lad20cd

    title = "".join(f"{obj} = {score:.2f}, " for obj, score in zip(objs, cov))
    title = title[:-2]
    title += f"\n(n = {n_sensors}, $\\theta$ = {theta} m)"

    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    plot_optimisation_result(
        coverage,
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
    save_fig(
        fig,
        f"multiobj_wplace{round(cov[3], 2)}_child{round(cov[1], 2)}_theta{theta}_{n_sensors}sensors.png",
        save_dir,
    )


def fig_coverage_above_uo(
    uo_coverage: dict,
    scores: np.ndarray,
    objs: list,
    theta: float,
    n_uo_oa: int,
    all_groups: dict,
    save_dir: Path,
):
    """Create a swarm plot showing optimised networks that have higher coverage thab the
    pre-existing Urban Observatory network across all objectives. Figure name:
    multiobj_theta{theta}_{n_uo_oa}sensors_above_urbobs.png

    Parameters
    ----------
    uo_coverage : dict
        Coverage of each output area with the Urban Observatory network (e.g. from
        get_uo_coverage_oa)
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    objs : list
        Names of objectives in the order they appear in scores
    theta : float
        Coverage distance to use
    n_uo_oa : int
        Number of output area the Urban Observatory network has a sensor in
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    save_dir : Path
        Directory to save figure
    """
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    threshold = {
        all_groups["workplace"]["title"]: uo_coverage["workplace"]["total_coverage"],
        all_groups["pop_total"]["title"]: uo_coverage["pop_total"]["total_coverage"],
        all_groups["pop_children"]["title"]: uo_coverage["pop_children"][
            "total_coverage"
        ],
        all_groups["pop_elderly"]["title"]: uo_coverage["pop_elderly"][
            "total_coverage"
        ],
    }
    ax = networks_swarmplot(scores, objs, thresholds=threshold, ax=ax)
    ax.set_ylim([0, 1])
    save_fig(fig, f"multiobj_theta{theta}_{n_uo_oa}sensors_above_urbobs.png", save_dir)


def fig_max_min_coverage(
    lad20cd: str,
    scores: np.ndarray,
    objs: list,
    theta: float,
    n_sensors: int,
    solutions: np.ndarray,
    inputs: dict,
    save_dir: float,
):
    """Plot the network that maximises the minimum coverage across all objectives.

    Parameters
    ----------
    lad20cd : str
        Local authority code
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    objs : list
        Names of objectives in the order they appear in scores
    theta : float
        Coverage distance to use
    n_sensors : int
        No. of sensors in the network
    solutions : np.ndarray
        Sensor output area indices for each candidate network
    inputs : dict
        Optimisation inputs from networks_multi_objs.get_multi_obj_inputs
    save_dir : float
        Directory to save figure
    """
    # find network that has the maximum minimum coverage across all objectives
    # (i.e. find network where all objectives have a coverage of at least t, for
    # highest possible t)
    t = scores.min()
    delta = 0.001
    remaining = len(scores)
    while remaining > 0:
        t += delta
        remaining = (scores > t).all(axis=1).sum()
    t -= delta
    best_idx = (scores > t).all(axis=1).argmax()

    sensor_idx = solutions[best_idx].astype(int)
    sensor_dict = [
        {
            "oa11cd": inputs["oa11cd"][idx],
            "x": inputs["oa_x"][idx],
            "y": inputs["oa_y"][idx],
        }
        for idx in sensor_idx
    ]

    coverage = calc_coverage(
        lad20cd, sensor_dict, oa_weight=inputs["oa_weight"]["pop_total"], theta=theta
    )
    coverage["sensors"] = sensor_dict
    coverage["lad20cd"] = lad20cd

    title = "".join(
        f"{obj} = {score:.2f}, " for obj, score in zip(objs, scores[best_idx])
    )

    title = title[:-2]
    title += f"\n(n = {n_sensors}, $\\theta$ = {theta} m)"

    fig, ax = get_fig_grid(nrows_ncols=(1, 1))
    plot_optimisation_result(
        coverage,
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
    save_fig(
        fig,
        f"multiobj_compromise_theta{theta}_{n_sensors}sensors_cov{round(t, 3)}.png",
        save_dir,
    )


def main():
    """Save figures showing the results of running the multi-objective optimisation
    (with the NSGA2 algorithm)
    """
    print("Saving multi-objective network figures...")
    set_fig_style()
    config = get_config()

    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_path = get_multi_objs_filepath(config)
    networks = load_pickle(networks_path)

    figs_dir = get_figures_save_dir(config)

    theta, n_sensors = get_default_optimisation_params(config)
    n = networks[f"theta{theta}"][f"{n_sensors}sensors"]
    scores, solutions = extract_all(n)
    scores = -scores

    population_groups, all_groups = get_objectives(config)
    objs = [g["title"] for g in all_groups.values()]

    threshold = config["figures"]["multi_objectives"]["all_coverage_threshold"]
    fig_all_above_threshold(scores, objs, threshold, theta, n_sensors, figs_dir)

    threshold = config["figures"]["multi_objectives"]["work_coverage_threshold"]
    work_name = config["objectives"]["workplace"]["title"]
    fig_work_above_threshold(
        scores, objs, threshold, theta, n_sensors, work_name, figs_dir
    )

    child_name = config["objectives"]["population_groups"]["pop_children"]["title"]
    inputs = get_multi_obj_inputs(lad20cd, population_groups)
    fig_max_child_work_above_threshold(
        lad20cd,
        scores,
        objs,
        threshold,
        theta,
        n_sensors,
        solutions,
        inputs,
        work_name,
        child_name,
        figs_dir,
    )

    uo_sensors = load_uo_sensors(config)
    uo_coverage = get_uo_coverage_oa(
        lad20cd, None, theta, all_groups, inputs["oa_weight"]
    )
    n_uo_oa = uo_sensors["oa11cd"].nunique()
    fig_coverage_above_uo(
        uo_coverage, scores, objs, theta, n_uo_oa, all_groups, figs_dir
    )

    fig_max_min_coverage(
        lad20cd, scores, objs, theta, n_sensors, solutions, inputs, figs_dir
    )


if __name__ == "__main__":
    main()
