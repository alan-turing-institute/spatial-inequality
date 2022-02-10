from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from networks_multi_objs import get_multi_obj_inputs
from networks_two_objs import get_two_objs_filepath
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
    plot_optimisation_result,
    save_fig,
)


def fig_obj1_vs_obj2(
    plot_objs: list,
    scores: np.ndarray,
    all_groups: dict,
    theta: float,
    n_sensors: int,
    save_dir: Path,
):
    """Save a scatter plot showing the relationship between the coverage of one
    objective and another. Figure name: 2obj_theta{theta}_{n_sensors}sensors.png

    Parameters
    ----------
    plot_objs : list
        Names of the two objectives to plot
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    theta : float
        Coverage distance to use
    n_sensors : int
        Number of sensors in the candidate networks
    save_dir : Path
        Directory to save the figure
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))
    ax.plot(scores[:, 1], scores[:, 0], "o")
    ax.set_xlabel(all_groups[plot_objs[1]]["title"], fontsize=14)
    ax.set_ylabel(all_groups[plot_objs[0]]["title"], fontsize=14)
    ax.axis("equal")
    save_fig(fig, f"2obj_theta{theta}_{n_sensors}sensors.png", save_dir)


def fig_two_objs_spectrum(
    lad20cd: str,
    plot_objs: list,
    scores: np.ndarray,
    solutions: np.ndarray,
    inputs: dict,
    all_groups: dict,
    theta: float,
    n_sensors: int,
    save_dir: Path,
):
    """Save a figure showing a range of networks varying from maximal coverage of one
    objective to maximal coverage of another, showing the trade-offs between the two.
    Figure name: 2obj_spectrum_theta{theta}_{n_sensors}sensors.png

    Parameters
    ----------
    lad20cd : str
        Local authority code
    plot_objs : list
        Names of the two objectives to plot
    scores : np.ndarray
        Coverage values for each objective in each candidate network
    solutions : np.ndarray
        Output area indices for each sensor in each candidate network
    inputs : dict
        Optimisation inputs from networks_two_objs.get_two_obj_inputs
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    theta : float
        Coverage distance to use
    n_sensors : int
        Number of sensors in the candidate networks
    save_dir : Path
        Directory to save the figure
    """
    population_size = len(scores)
    rank_idx = scores[:, 0].argsort()
    ranks_to_plot = np.linspace(0, population_size - 1, 4).astype(int)

    fig, ax = get_fig_grid()
    for i, rank in enumerate(ranks_to_plot):
        idx = rank_idx[rank]
        sensor_idx = solutions[idx].astype(int)
        sensor_dict = [
            {
                "oa11cd": inputs["oa11cd"][idx],
                "x": inputs["oa_x"][idx],
                "y": inputs["oa_y"][idx],
            }
            for idx in sensor_idx
        ]
        coverage = calc_coverage(
            lad20cd,
            sensor_dict,
            oa_weight=inputs["oa_weight"][plot_objs[0]],
            theta=theta,
        )
        coverage["sensors"] = sensor_dict
        coverage["lad20cd"] = lad20cd

        title = "".join(
            f"{all_groups[obj]['title']} = {score:.2f}, "
            for obj, score in zip(["pop_elderly", "workplace"], scores[idx])
        )
        title = title[:-2]

        plot_optimisation_result(
            coverage,
            title=title,
            ax=ax[i],
            show=False,
            legend=False,
            sensor_size=50,
            sensor_color="green",
            sensor_edgecolor="yellow",
            sensor_linewidth=1.5,
        )

    add_scalebar(ax[1])
    add_colorbar(ax[-1], cmap="Greens", label="Coverage")
    fig.suptitle(f"n = {n_sensors}, $\\theta$ = {theta} m", y=0.87, fontsize=20)
    save_fig(fig, f"2obj_spectrum_theta{theta}_{n_sensors}sensors.png", save_dir)


def main():
    """
    Save figures showing the results of running the mulit-objective optimisation (NSGA2)
    with two objectives.
    """
    print("Saving two-objective network figures...")
    set_fig_style()
    config = get_config()
    figs_dir = get_figures_save_dir(config)

    networks_path = get_two_objs_filepath(config)
    networks = load_pickle(networks_path)
    theta, n_sensors = get_default_optimisation_params(config)
    n = networks[f"theta{theta}"][f"{n_sensors}sensors"]
    scores, solutions = extract_all(n)
    scores = -scores

    population_groups, all_groups = get_objectives(config)
    plot_objs = config["optimisation"]["two_objectives"]["objectives"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    inputs = get_multi_obj_inputs(lad20cd, population_groups)

    fig_obj1_vs_obj2(plot_objs, scores, all_groups, theta, n_sensors, figs_dir)
    fig_two_objs_spectrum(
        lad20cd,
        plot_objs,
        scores,
        solutions,
        inputs,
        all_groups,
        theta,
        n_sensors,
        figs_dir,
    )


if __name__ == "__main__":
    main()
