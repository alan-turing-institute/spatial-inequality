import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from spineq.optimise import calc_coverage
from spineq.plotting import (
    get_fig_grid,
    add_colorbar,
    save_fig,
    add_scalebar,
    plot_optimisation_result,
    networks_swarmplot,
)
from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.genetic import extract_all
from figs_urb_obs import get_uo_coverage_oa, load_uo_sensors
from networks_multi_objs import get_multi_obj_inputs
from utils import get_config, set_fig_style, load_pickle


def fig_obj1_vs_obj2(plot_objs, scores, all_groups, theta, n_sensors, save_dir):
    fig, ax = plt.subplots(1, 1, figsize=(8, 3))
    ax.plot(scores[:, 0], scores[:, 1], "o")
    ax.set_ylabel(all_groups[plot_objs[0]]["title"], fontsize=14)
    ax.set_xlabel(all_groups[plot_objs[1]]["title"], fontsize=14)
    ax.axis("equal")

    save_fig(fig, f"2obj_theta{theta}_{n_sensors}sensors.png", save_dir)


def fig_two_objs_spectrum(
    lad20cd,
    plot_objs,
    scores,
    solutions,
    inputs,
    all_groups,
    theta,
    n_sensors,
    save_dir,
):
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
    fig.suptitle(f"n = 55, $\\theta$ = 500 m", y=0.87, fontsize=20)
    save_fig(fig, f"2obj_spectrum_theta{theta}_{n_sensors}sensors.png", save_dir)


def main():
    set_fig_style()
    config = get_config()

    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_dir = config["optimisation"]["networks_dir"]
    filename = config["optimisation"]["two_objectives"]["filename"]
    networks_path = Path(save_dir, lad20cd, networks_dir, filename)
    networks = load_pickle(networks_path)

    figs_dir = config["figures"]["save_dir"]
    save_path = Path(save_dir, lad20cd, figs_dir)
    os.makedirs(save_path, exist_ok=True)

    theta = config["optimisation"]["theta"]["default"]
    n_sensors = config["optimisation"]["n_sensors"]["default"]
    n = networks[f"theta{theta}"][f"{n_sensors}sensors"]
    scores, solutions = extract_all(n)
    scores = -scores

    population_groups = config["objectives"]["population_groups"]
    all_groups = dict(population_groups)
    all_groups["workplace"] = config["objectives"]["workplace"]
    plot_objs = config["optimisation"]["two_objectives"]["objectives"]
    inputs = get_multi_obj_inputs(lad20cd, population_groups)

    fig_obj1_vs_obj2(plot_objs, scores, all_groups, theta, n_sensors, save_path)
    fig_two_objs_spectrum(
        lad20cd,
        plot_objs,
        scores,
        solutions,
        inputs,
        all_groups,
        theta,
        n_sensors,
        save_path,
    )


if __name__ == "__main__":
    main()
