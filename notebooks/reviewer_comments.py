import pickle

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import geopandas as gpd
import pandas as pd
from matplotlib import cm, colors
import matplotlib.transforms as mtransforms
from pandas.plotting import parallel_coordinates
from pygmo import fast_non_dominated_sorting, hypervolume

from spineq.genetic import extract_all
from spineq.data_fetcher import get_oa_centroids
from spineq.optimise import get_optimisation_inputs, calc_coverage
from spineq.plotting import save_fig

plt.style.use("fivethirtyeight")
mpl.rcParams["figure.facecolor"] = "white"
mpl.rcParams["axes.facecolor"] = "white"
mpl.rcParams["axes.grid"] = False
mpl.rcParams["savefig.facecolor"] = "white"
mpl.rcParams["font.size"] = 6.5


# ## parallel coords

with open(
    "/Users/jroberts/GitHub/spatial-inequality/publications/OptimisingForEquity/results/E08000021_updated_10k/networks/networks_multiobj.pkl",
    "rb",
) as f:
    d = pickle.load(f)

r = d["theta500"]["55sensors"]

scores, sensors = extract_all(r)
scores = -scores

objs = ["Total Residents", "Residents Under 16", "Residents Over 65", "Workers"]

scores = pd.DataFrame(scores, columns=objs)
scores["rank_workers"] = scores["Workers"].rank()
scores["rank_o65"] = scores["Residents Over 65"].rank()
scores["rank_u16"] = scores["Residents Under 16"].rank()
scores["rank_t"] = scores["Total Residents"].rank()


rank_cols = ["rank_workers", "rank_o65", "rank_u16", "rank_t"]
rank_labels = {
    "rank_workers": "Workplace rank",
    "rank_o65": "Over 65s rank",
    "rank_u16": "Under 16s rank",
    "rank_t": "Total Residents rank",
}
obj_order = ["Residents Over 65", "Residents Under 16", "Total Residents", "Workers"]
for rc in rank_cols:
    fig, ax = plt.subplots(1, 1, figsize=(6, 3))
    parallel_coordinates(
        scores.sort_values(by=rc)[obj_order + [rc]],
        rc,
        colormap="plasma",
        linewidth=1,
        ax=ax,
    )
    ax.set_ylabel("Coverage")
    ax.set_xlim([-0.1, 3.1])

    # hide legend labels for individual networks
    ax.legend().remove()

    cb = fig.colorbar(
        cm.ScalarMappable(
            norm=colors.Normalize(vmin=0, vmax=len(scores) - 1), cmap="plasma"
        )
    )
    cb.set_ticks([0, 49, 99, 149, 199])
    cb.set_ticklabels([200, 150, 100, 50, 1])
    cb.set_label(rank_labels[rc], fontsize=8)
    # ax.axhline(0.45, color="k", linestyle="--", linewidth=3)

    save_fig(fig, f"parallel_{rc}", "paper_figures", ".tiff")


scores["above45"] = (scores[objs] > 0.45).all(axis=1)
scores["above45"] = scores["above45"].replace(
    {True: "All $>0.45$", False: "At least one $\leq0.45$"}
)
plt.figure(figsize=(6, 3))
parallel_coordinates(
    scores[obj_order + ["above45"]], "above45", color=["pink", "blue"], linewidth=1
)


plt.axhline(0.45, color="k", linestyle="--", linewidth=3)
plt.ylabel("Coverage")
plt.legend(loc="upper left", framealpha=1.0)
plt.xlim([-0.1, 3.1])

save_fig(plt.gcf(), f"parallel_above45", "paper_figures", ".tiff")

rc = "rank_workers"
fig, ax = plt.subplots(1, 2, figsize=(7, 3), sharex=True)
parallel_coordinates(
    scores.sort_values(by=rc)[obj_order + [rc]],
    rc,
    colormap="plasma",
    linewidth=1,
    ax=ax[0],
)
ax[0].set_ylabel("Coverage")
ax[0].set_xlim([-0.1, 3.1])

# hide legend labels for individual networks
ax[0].legend().remove()
cb = fig.colorbar(
    cm.ScalarMappable(
        norm=colors.Normalize(vmin=0, vmax=len(scores) - 1), cmap="plasma"
    ),
    ax=ax[0],
    location="bottom",
    anchor=(0.5, -0.1),
    use_gridspec=False,
    shrink=0.9,
)
cb.set_ticks([0, 49, 99, 149, 199])
cb.set_ticklabels([200, 150, 100, 50, 1])
cb.ax.set_ylabel("Workers rank", fontsize=14, rotation=0, labelpad=100, loc="bottom")

scores["above45"] = (scores[objs] > 0.45).all(axis=1)
scores["above45"] = scores["above45"].replace(
    {True: "All $>0.45$", False: "At least one $\leq0.45$"}
)


parallel_coordinates(
    scores[obj_order + ["above45"]],
    "above45",
    color=["pink", "blue"],
    linewidth=1,
    ax=ax[1],
)

ax[1].axhline(0.45, color="k", linestyle="--", linewidth=3, label="0.45 Threshold")
ax[1].set_ylabel("Coverage")
ax[1].legend(loc="upper center", framealpha=1.0, bbox_to_anchor=(0.48, -0.1), ncol=3)
ax[1].set_xlim([-0.1, 3.1])

fig.tight_layout()

save_fig(fig, f"parallel_{rc}_over45", "paper_figures", ".tiff")

best_idx = scores[objs].idxmax()
scores["display"] = "_"

plt.figure(figsize=(6, 3))
parallel_coordinates(
    scores[obj_order + ["display"]],  # display
    "display",  # display
    color=["lightgrey", "blue", "red", "green", "orange"],
    linewidth=0.5,
)

color = ["blue", "red", "magenta", "orange"]
marker = ["s", "^", "x", "o"]
for c, m, idx, name in zip(color, marker, best_idx, best_idx.index):
    scores[obj_order].iloc[idx].plot(
        linewidth=2, color=c, marker=m, label=f"Max {name}", zorder=3, markersize=10
    )

plt.ylabel("Coverage")
plt.legend(loc="upper left", framealpha=1.0)
plt.xlim([-0.1, 3.1])

save_fig(plt.gcf(), f"parallel_highlightMax", "paper_figures", ".tiff")


best_idx = scores[objs].idxmax()
scores["display"] = "_"

plt.figure(figsize=(6, 3))
parallel_coordinates(
    scores[obj_order + ["above45"]],  # display
    "above45",  # display
    color=["pink", "blue", "red", "green", "orange"],
    linewidth=1,
)

color = ["orange", "red", "magenta", "green"]
marker = ["s", "^", "x", "o"]
for c, m, idx, name in zip(color, marker, best_idx, best_idx.index):
    scores[obj_order].iloc[idx].plot(
        linewidth=3, color=c, marker=m, label=f"Max {name}", zorder=3, markersize=12
    )


plt.ylabel("Coverage")
plt.legend(loc="upper left", framealpha=1.0)
plt.xlim([-0.1, 3.1])
plt.axhline(0.45, color="k", linestyle="--")

save_fig(plt.gcf(), f"parallel_highlightMax", "paper_figures", ".tiff")


scores["workabove65"] = scores["Workers"] > 0.65
scores["workabove65"] = scores["workabove65"].replace(
    {True: "Workers coverage $>0.65$", False: "Workers coverage $\leq0.65$"}
)
plt.figure(figsize=(7, 4))
parallel_coordinates(
    scores[obj_order + ["workabove65"]],
    "workabove65",
    color=["blue", "pink"],
    linewidth=1,
)
plt.axhline(0.65, color="k", linestyle="--", linewidth=3)
plt.ylabel("Coverage")
plt.legend(loc="upper left")


uo_sensors = gpd.read_file(
    "/Users/jroberts/GitHub/spatial-inequality/publications/OptimisingForEquity/results/E08000021_updated_10k/urb_obs"
)

sensor_oa = uo_sensors["oa11cd"].unique()
oa_centroids = get_oa_centroids()
uo_sensor_dict = (
    oa_centroids[oa_centroids.index.isin(sensor_oa)][["x", "y"]]
    .reset_index()
    .to_dict(orient="records")
)

pop_age_groups = {
    "pop_total": {"min": 0, "max": 90, "weight": 1},
    "pop_children": {"min": 0, "max": 15, "weight": 1},
    "pop_elderly": {"min": 65, "max": 90, "weight": 1},
}
oa_weight = get_optimisation_inputs(
    population_weight=1,
    workplace_weight=1,
    pop_age_groups=pop_age_groups,
    combine=False,
)

uo_coverage = {}
for name, weight in oa_weight["oa_weight"].items():
    uo_coverage[name] = calc_coverage(
        "E08000021", [x["oa11cd"] for x in uo_sensor_dict], oa_weight=weight, theta=500
    )["total_coverage"]

scores["aboveuo"] = (
    (scores["Workers"] > uo_coverage["workplace"])
    & (scores["Residents Under 16"] > uo_coverage["pop_children"])
    & (scores["Residents Over 65"] > uo_coverage["pop_elderly"])
    & (scores["Total Residents"] > uo_coverage["pop_total"])
)
scores["aboveuo"] = scores["aboveuo"].replace(
    {True: "All higher than UO", False: "Workers lower than UO"}
)

plt.figure(figsize=(6, 3))
parallel_coordinates(
    scores[obj_order + ["aboveuo"]], "aboveuo", color=["blue", "pink"], linewidth=1
)
plt.plot(
    [0, 1, 2, 3],
    [
        uo_coverage["pop_elderly"],
        uo_coverage["pop_children"],
        uo_coverage["pop_total"],
        uo_coverage["workplace"],
    ],
    "ko-",
    markersize=7,
    label="Urban Observatory",
    linewidth=1.5,
)
plt.legend(framealpha=1.0)
plt.ylabel("Coverage")
plt.xlim([-0.1, 3.1])

save_fig(plt.gcf(), f"parallel_aboveUO", "paper_figures", ".tiff")


raw_scores, _ = extract_all(r)

# random networks

n_oa = len(oa_centroids)
n_networks = 10000
n_sensors = 55

rnd_oa = np.random.choice(oa_centroids.index, size=(n_networks, n_sensors))

from tqdm import trange

rnd_scores = np.array(
    [
        [
            calc_coverage("E08000021", rnd_oa[i, :], oa_weight=w, theta=500)[
                "total_coverage"
            ]
            for w in oa_weight["oa_weight"].values()
        ]
        for i in trange(rnd_oa.shape[0])
    ]
)

rnd_scores = pd.DataFrame(rnd_scores, columns=objs)
rnd_scores["type"] = "Random"
scores["type"] = "NSGA-II"

all_scores = pd.concat([scores[objs + ["type"]], rnd_scores[objs + ["type"]]])
ndf, dl, dc, ndr = fast_non_dominated_sorting(rnd_scores[objs].values)
rnd_hyper = hypervolume(-rnd_scores[objs].values).compute([0, 0, 0, 0])

# greedy

with open("tmp_greedy_4obj.pkl", "rb") as f:
    greedy = pickle.load(f)

greedy_scores = greedy["coverage"]
greedy_scores["type"] = "Greedy"
greedy_scores = greedy_scores.rename(
    columns={
        "pop_total": "Total Residents",
        "pop_children": "Residents Under 16",
        "pop_elderly": "Residents Over 65",
        "workplace": "Workers",
    }
)

# convergence
with open(
    "/Users/jroberts/GitHub/spatial-inequality/publications/OptimisingForEquity/results/E08000021_custom_log/networks/networks_multiobj.pkl_theta500_55sensors.log",
    "rb",
) as f:
    tmp = pickle.load(f)

fig, ax = plt.subplots(1, 2, figsize=(7, 3))

ax[1].plot(tmp["generations"], tmp["hypervolume"], label="NSGA-II")
ax[1].axhline(
    rnd_hyper, color="k", linestyle="--", label="10k random networks", linewidth=1
)
# ax[0].legend()

markers = ["o", "^", "s", "x"]
for o, f, m in zip(objs, range(np.array(tmp["fitness"]).shape[1]), markers):
    ax[0].plot(
        tmp["generations"],
        -np.array(tmp["fitness"])[:, f],
        label=o,
        marker=m,
        markevery=20,
        linewidth=1.5,
    )
for i, v in enumerate(greedy_scores[objs].max().values):
    if i == 0:
        label = "Max single-objective (greedy)"
    else:
        label = None
    ax[0].axhline(v, color="k", linestyle="--", linewidth=1, label=label)

# for v in scores[objs].max().values:
#    ax[1].plot(20000, v, "ko")

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
save_fig(fig, "converge", "paper_figures", ".tiff")
