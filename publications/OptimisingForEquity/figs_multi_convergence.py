import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.transforms as mtransforms
from pathlib import Path

from pygmo import hypervolume

from spineq.plotting import save_fig

from utils import (
    get_networks_save_dir,
    load_pickle,
    set_fig_style,
    get_config,
    get_all_optimisation_params,
    get_objectives,
    get_figures_params,
)
from networks_single_obj import get_single_obj_filepath


def plot_convergence_metrics(
    multi_log: dict,
    objectives: list,
    rnd_scores: np.ndarray,
    single_scores: list,
    filename: str,
    save_dir: Path,
    extension: str,
):
    """Save convergence figures - hypervolume vs. number of generations and maximum
    coverage of each objective vs. number of generations.

    Parameters
    ----------
    multi_log : dict
        Log of population hypervolume and maximum coverage as saved by
        networks_multi_obj.py
    objectives : list
        List of objective names (in the order they appear in coverage scores)
    rnd_scores : np.ndarray
        Array of coverage scores for random networks generated with networks_random.py
    single_scores : list
        List of coverage achieved with the greedy algorithm (extracted from the results
        of networks_single_obj.py)
    filename : str
        File name of the figure to save (excluding directory and extension)
    save_dir : Path
        Directory to save the figure in
    extension : str
        Format to save the figure in
    """
    rnd_hyper = hypervolume(-rnd_scores).compute([0, 0, 0, 0])

    fig, ax = plt.subplots(1, 2, figsize=(7, 3))
    ax[1].plot(multi_log["generations"], multi_log["hypervolume"], label="NSGA-II")
    ax[1].axhline(
        rnd_hyper, color="k", linestyle="--", label="10k random networks", linewidth=1
    )

    markers = ["o", "^", "s", "x"]
    for o, f, m in zip(
        objectives, range(np.array(multi_log["fitness"]).shape[1]), markers
    ):
        ax[0].plot(
            multi_log["generations"],
            -np.array(multi_log["fitness"])[:, f],
            label=o,
            marker=m,
            markevery=20,
            linewidth=1.5,
        )
    for i, v in enumerate(single_scores):
        label = "Max single-objective (greedy)" if i == 0 else None
        ax[0].axhline(v, color="k", linestyle="--", linewidth=1, label=label)

    ax[0].set_ylabel("Coverage")
    ax[0].legend()
    ax[1].set_ylabel("Hypervolume")

    fig.tight_layout()
    labels = ["A)", "B)"]
    for i, a in enumerate(ax):
        a.set_xlabel("Generations")
        a.set_xlim([0, 20000])
        trans = mtransforms.ScaledTranslation(-30 / 72, 16 / 72, fig.dpi_scale_trans)
        a.text(
            0.0,
            1.0,
            labels[i],
            transform=a.transAxes + trans,
            horizontalalignment="left",
            verticalalignment="top",
            fontsize=mpl.rcParams["axes.titlesize"],
        )
    save_fig(fig, filename, save_dir, extension)


def main():
    """
    Save figures showing the convergence of the multi-objective algorithm over
    generations and comparisons with the single-objective results.
    """
    set_fig_style()

    config = get_config()
    networks_dir = get_networks_save_dir(config)

    single_networks_path = get_single_obj_filepath(config)
    single_results = load_pickle(single_networks_path)

    rnd_results = load_pickle(
        Path(networks_dir, config["optimisation"]["random"]["filename"])
    )

    thetas, n_sensors = get_all_optimisation_params(config)
    _, all_groups = get_objectives(config)
    objectives = [g["title"] for g in all_groups.values()]

    fig_dir, extension = get_figures_params(config)

    for t in thetas:
        for ns in n_sensors:
            multi_log_path = Path(
                networks_dir, f"networks_multiobj.pkl_theta{t}_{ns}sensors.log"
            )
            multi_log = load_pickle(multi_log_path)
            rnd_scores = rnd_results[f"theta{t}"][f"{ns}sensors"]
            single_scores = [
                single_results[o][f"theta{t}"][f"{ns}sensors"]["coverage_history"][-1]
                for o in single_results.keys()
            ]
            filename = f"convergence_theta{t}_{ns}sensors"
            plot_convergence_metrics(
                multi_log,
                objectives,
                rnd_scores,
                single_scores,
                filename,
                fig_dir,
                extension,
            )


if __name__ == "__main__":
    main()
