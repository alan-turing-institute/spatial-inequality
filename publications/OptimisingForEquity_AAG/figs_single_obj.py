from math import floor, ceil, sqrt
import matplotlib.pyplot as plt
from spineq.plotting import (
    get_fig_grid,
    add_colorbar,
    save_fig,
    add_scalebar,
    plot_optimisation_result,
)
from networks_single_obj import get_single_obj_filepath
from utils import (
    get_config,
    set_fig_style,
    load_pickle,
    get_objectives,
    get_default_optimisation_params,
    get_all_optimisation_params,
    get_figures_save_dir,
)


def fig_single_obj(thetas, n_sensors, results, all_groups, save_dir):
    n_figs = len(thetas) * len(n_sensors)
    n_rows = floor(sqrt(n_figs))
    n_cols = ceil(n_figs / n_rows)
    for plot_obj in all_groups.keys():
        fig, grid = get_fig_grid(nrows_ncols=(n_rows, n_cols))
        i = 0
        for t in thetas:
            for s in n_sensors:
                r = results[plot_obj][f"theta{t}"][f"{s}sensors"]
                plot_optimisation_result(
                    r,
                    title=f"n = {s}, $\\theta$ = {t} m, c = {r['total_coverage']:.2f}",
                    ax=grid[i],
                    show=False,
                    legend=False,
                    sensor_size=50,
                    sensor_color="green",
                    sensor_edgecolor="yellow",
                    sensor_linewidth=1.5,
                )
                if i == 1:
                    add_scalebar(grid[i])

                i += 1

        add_colorbar(grid[-1], label="Coverage", cmap="Greens")

        fig.suptitle(all_groups[plot_obj]["title"], y=0.87, fontsize=20)
        t_str = "theta" + "_".join(str(t) for t in thetas)
        n_str = "nsensors" + "_".join(str(n) for n in n_sensors)
        save_fig(fig, f"{plot_obj}_{t_str}_{n_str}.png", save_dir)


def fig_coverage_vs_sensors(results, theta, n_sensors, all_groups, save_dir):
    fig, ax = plt.subplots(1, 1)
    for obj in all_groups.keys():
        cov_history = results[obj][f"theta{theta}"][f"{n_sensors}sensors"][
            "coverage_history"
        ]
        ax.plot(
            range(1, len(cov_history) + 1), cov_history, label=all_groups[obj]["title"]
        )

    ax.set_xlabel("No. Sensors")
    ax.set_ylabel("Coverage")
    ax.legend()
    save_fig(fig, "coverage_vs_nsensors.png", save_dir)


def main():
    set_fig_style()

    config = get_config()
    networks_path = get_single_obj_filepath(config)
    results = load_pickle(networks_path)

    figs_dir = get_figures_save_dir(config)

    thetas, n_sensors = get_all_optimisation_params(config)
    _, all_groups = get_objectives(config)
    fig_single_obj(thetas, n_sensors, results, all_groups, figs_dir)

    theta, n_sensors = get_default_optimisation_params(config)
    fig_coverage_vs_sensors(results, theta, n_sensors, all_groups, figs_dir)


if __name__ == "__main__":
    main()
