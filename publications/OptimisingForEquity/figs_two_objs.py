from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from networks_two_objs import get_two_objs_filepath
from utils import (
    add_subplot_label,
    get_config,
    get_default_optimisation_params,
    get_figures_params,
    get_objectives,
    load_jsonpickle,
    set_fig_style,
)

from spineq.opt.result import PopulationResult
from spineq.plot.plotting import (
    add_colorbar,
    add_scalebar,
    get_fig_grid,
    plot_optimisation_result,
    save_fig,
)


def fig_obj1_vs_obj2(
    plot_objs: list,
    result: PopulationResult,
    all_groups: dict,
    theta: float,
    n_sensors: int,
    save_dir: Path,
    extension: str,
):
    """Save a scatter plot showing the relationship between the coverage of one
    objective and another. Figure name: 2obj_theta{theta}_{n_sensors}sensors.png

    Parameters
    ----------
    plot_objs : list
        Names of the two objectives to plot
    result : PopulationResult
        Optimisation results
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    theta : float
        Coverage distance to use
    n_sensors : int
        Number of sensors in the candidate networks
    save_dir : Path
        Directory to save the figure
    extension : str
        Figure file format
    """
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))
    ax.plot(result.total_coverage[:, 1], result.total_coverage[:, 0], "o")
    ax.set_xlabel(all_groups[plot_objs[1]]["title"], fontsize=14)
    ax.set_ylabel(all_groups[plot_objs[0]]["title"], fontsize=14)
    ax.axis("equal")
    save_fig(fig, f"2obj_theta{theta}_{n_sensors}sensors", save_dir, extension)


def fig_two_objs_spectrum(
    plot_objs: list,
    result: PopulationResult,
    all_groups: dict,
    theta: float,
    n_sensors: int,
    save_dir: Path,
    extension: str,
):
    """Save a figure showing a range of networks varying from maximal coverage of one
    objective to maximal coverage of another, showing the trade-offs between the two.
    Figure name: 2obj_spectrum_theta{theta}_{n_sensors}sensors.png

    Parameters
    ----------
    plot_objs : list
        Names of the two objectives to plot
    result : PopulationResult
        Optimisation results
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
    extension : str
        Figure file format
    """
    rank_idx = result.total_coverage[:, 0].argsort()
    ranks_to_plot = np.linspace(0, result.population_size - 1, 4).astype(int)

    fig, ax = get_fig_grid()
    for i, rank in enumerate(ranks_to_plot):
        idx = rank_idx[rank]

        title = "".join(
            f"{all_groups[obj]['title']} = {score:.2f}, "
            for obj, score in zip(plot_objs, result.total_coverage[idx])
        )
        title = title[:-2]

        plot_optimisation_result(
            result.get_single_result(idx),
            title=title,
            ax=ax[i],
            show=False,
            legend=False,
            sensor_size=20,
            sensor_color="green",
            sensor_edgecolor="yellow",
            sensor_linewidth=1,
        )
        add_subplot_label(fig, ax[i], i)

    add_scalebar(ax[1])
    add_colorbar(ax[-1], cmap="Greens", label="Coverage")
    save_fig(fig, f"2obj_spectrum_theta{theta}_{n_sensors}sensors", save_dir, extension)


def main():
    """
    Save figures showing the results of running the mulit-objective optimisation (NSGA2)
    with two objectives.
    """
    print("Saving two-objective network figures...")
    set_fig_style()
    config = get_config()
    figs_dir, extension = get_figures_params(config)
    _, all_groups = get_objectives(config)
    plot_objs = config["optimisation"]["two_objectives"]["objectives"]
    networks_path = get_two_objs_filepath(config)
    networks = load_jsonpickle(networks_path)
    theta, n_sensors = get_default_optimisation_params(config)
    result = networks[f"theta{theta}"][f"{n_sensors}sensors"][0]

    fig_obj1_vs_obj2(
        plot_objs, result, all_groups, theta, n_sensors, figs_dir, extension
    )
    fig_two_objs_spectrum(
        plot_objs,
        result,
        all_groups,
        theta,
        n_sensors,
        figs_dir,
        extension,
    )


if __name__ == "__main__":
    main()
