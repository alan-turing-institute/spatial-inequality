from spineq.optimise import calc_oa_weights
from spineq.plotting import (
    get_fig_grid,
    plot_oa_importance,
    add_colorbar,
    save_fig,
    add_scalebar,
    plot_oa_weights,
)
from spineq.data_fetcher import lad20nm_to_lad20cd, get_oa_shapes, get_oa_stats
from utils import (
    set_fig_style,
    get_objectives,
    get_config,
    get_default_optimisation_params,
    get_figures_save_dir,
)


def get_weights(lad20cd, population_groups):
    oa_weights = {
        name: calc_oa_weights(
            lad20cd=lad20cd,
            pop_age_groups={name: weights},
            population_weight=1,
            workplace_weight=0,
        )
        for name, weights in population_groups.items()
    }
    oa_weights["workplace"] = calc_oa_weights(
        lad20cd=lad20cd, population_weight=0, workplace_weight=1
    )
    return oa_weights


def calc_oa_density(lad20cd, all_groups, population_groups):
    oa = get_oa_shapes(lad20cd)
    oa["area"] = oa["geometry"].area / 1e6  # km^2

    stats = get_oa_stats(lad20cd)
    for name, config in population_groups.items():
        group_pop = (
            stats["population_ages"]
            .loc[
                :,
                (stats["population_ages"].columns >= config["min"])
                & (stats["population_ages"].columns <= config["max"]),
            ]
            .sum(axis=1)
        )
        group_pop.name = name
        oa = oa.join(group_pop)

    workplace = stats["workplace"]
    workplace.name = "workplace"
    oa = oa.join(workplace)

    for group in all_groups.keys():
        oa[f"{group}_perc"] = oa[group] / oa[group].sum()
        oa[f"{group}_reld"] = oa[f"{group}_perc"] / oa["area"]

    return oa


def fig_importance(lad20cd, groups, oa_weights, theta, save_dir, vmax=0.06):
    fig, grid = get_fig_grid()

    for i, g in enumerate(groups.items()):
        name = g[0]
        title = g[1]["title"]
        plot_oa_importance(
            lad20cd,
            oa_weights[name],
            theta=theta,
            vmax=vmax,
            ax=grid[i],
            show=False,
            legend=False,
            title=title,
        )
        if i == 1:
            add_scalebar(grid[i])

    add_colorbar(grid[-1], vmax=vmax, label="Importance")
    save_fig(fig, "demographics_importance.png", save_dir)


def fig_density(lad20cd, oa, all_groups, save_dir, vmax=6):
    fig, grid = get_fig_grid()

    for i, g in enumerate(all_groups.items()):
        name = g[0]
        title = g[1]["title"]
        plot_oa_weights(
            lad20cd,
            100 * oa[f"{name}_reld"],
            title=title,
            vmax=vmax,
            ax=grid[i],
            legend=False,
            show=False,
        )
        if i == 1:
            add_scalebar(grid[i])

    add_colorbar(grid[-1], vmax=vmax, label="Density [% / $\mathrm{km}^2$]")
    save_fig(fig, "demographics_density.png", save_dir)


def main():
    set_fig_style()

    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    figs_dir = get_figures_save_dir(config)

    theta, _ = get_default_optimisation_params(config)
    population_groups, all_groups = get_objectives(config)

    oa_weights = get_weights(lad20cd, population_groups)
    fig_importance(lad20cd, all_groups, oa_weights, theta, figs_dir)
    oa = calc_oa_density(lad20cd, all_groups, population_groups)
    fig_density(lad20cd, oa, all_groups, figs_dir)


if __name__ == "__main__":
    main()
