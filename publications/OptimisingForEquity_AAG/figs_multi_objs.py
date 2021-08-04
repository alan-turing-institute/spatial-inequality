import matplotlib.pyplot as plt
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
from networks_multi_objs import get_multi_obj_inputs, get_multi_objs_filepath
from utils import (
    get_config,
    set_fig_style,
    load_pickle,
    get_objectives,
    get_default_optimisation_params,
    get_figures_save_dir,
)


def fig_all_above_threshold(scores, objs, threshold, theta, n_sensors, save_dir):
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    networks_swarmplot(scores, objs, thresholds=threshold, ax=ax)
    save_fig(
        fig,
        f"multiobj_theta{theta}_{n_sensors}sensors_above{round(threshold * 100)}cov.png",
        save_dir,
    )


def fig_work_above_threshold(
    scores, objs, threshold, theta, n_sensors, work_name, save_dir
):
    work_idx = objs.index(work_name)
    if (scores[:, work_idx] < threshold).all():
        print(f"No networks with workplace coverage > {threshold}, skipping figure")
        return

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    networks_swarmplot(scores, objs, thresholds={work_name: threshold}, ax=ax)
    save_fig(
        fig,
        f"multiobj_theta{theta}_{n_sensors}sensors_workabove{threshold * 100}cov.png",
        save_dir,
    )


def fig_max_child_work_above_threshold(
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
    save_dir,
):
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

    coverage = calc_coverage(
        lad20cd, sensor_dict, oa_weight=inputs["oa_weight"][objs[0]], theta=theta
    )
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
    uo_coverage, scores, objs, theta, n_uo_oa, all_groups, save_dir
):
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
    lad20cd,
    scores,
    objs,
    theta,
    n_sensors,
    solutions,
    inputs,
    save_dir,
):
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