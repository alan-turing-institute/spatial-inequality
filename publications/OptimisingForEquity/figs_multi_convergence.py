import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import matplotlib.transforms as mtransforms
from pygmo import hypervolume

from spineq.plotting import save_fig

from utils import set_fig_style


def plot_convergence_metrics(
    multi_log, objectives, rnd_scores, single_scores, filename, save_dir, extension
):

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
    set_fig_style()

    objectives = None  # TODO: Load from config
    thetas = None
    n_sensors = None
    extension = None
    fig_dir = None
    rnd_results = None  # TODO: Load random networks from file
    single_results = None  # TODO: Load single obj results

    for t in thetas:
        for ns in n_sensors:
            multi_log = None  # TODO: load log of multi-objective metrics
            rnd_scores = rnd_results[
                ...
            ]  # TODO: Get results for number of sensors and theta value
            single_scores = [
                single_results[o][f"theta{t}"][f"{ns}sensors"]["coverage_history"][-1]
                for o in objectives
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
