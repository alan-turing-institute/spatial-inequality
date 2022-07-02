from pathlib import Path

import geopandas as gpd
from utils import (
    add_subplot_label,
    get_config,
    get_default_optimisation_params,
    get_figures_params,
    get_objectives,
    set_fig_style,
)

from spineq.data.fetcher import get_oa_shapes, get_oa_stats, lad20nm_to_lad20cd
from spineq.optimise import calc_oa_weights
from spineq.plotting import (
    add_colorbar,
    add_scalebar,
    get_fig_grid,
    plot_oa_importance,
    plot_oa_weights,
    save_fig,
)


def get_weights(lad20cd: str, population_groups: dict) -> dict:
    """Calculate optimisation weights for each objective for each output area
    in a local authority.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    population_groups : dict
        Parameters for residential population objectives, as returned by
        utils.get_objectives

    Returns
    -------
    dict
        Output area weights
    """
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


def calc_oa_density(
    lad20cd: str, all_groups: dict, population_groups: dict
) -> gpd.GeoDataFrame:
    """Calculate the density of people for each objective in each output area (OA),
    expressed as the percentage of people in that OA divided by the aera of the OA

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    all_groups : dict
        Short name (keys) and long title (values) for each objective.
    population_groups : dict
        Parameters for residential population objectives, as returned by
        utils.get_objectives

    Returns
    -------
    gpd.GeoDataFrame
        Data frame with popluation counts for each objective in each  outputa area, plus
        columns {name}_perc, {name}_reld for the percentage and density of people in
        each output area for each objective (where {name} is replaced with the name of
        the objective)
    """
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
    for group in all_groups:
        oa[f"{group}_perc"] = oa[group] / oa[group].sum()
        oa[f"{group}_reld"] = oa[f"{group}_perc"] / oa["area"]

    return oa


def fig_importance(
    lad20cd: str,
    groups: dict,
    oa_weights: dict,
    theta: float,
    save_dir: Path,
    extension: str,
    vmax: float = 0.06,
):
    """Save a figure showing the "importance" of each output area for each objective,
    where importance is the overall coverage of the whole local authority provided
    by a network with a single sensor placed in that output area. Name of figure:
    demographics_importance.png

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    groups : dict
        Name and title of each population group/objective
    oa_weights : dict
        Weight for each output area for each group/objective
    theta : float
        Coverage distance
    save_dir : Path
        Directory to save figure in
    extension : str
        Figure file format
    vmax : float, optional
        Max value for colour scale, by default 0.06
    """
    fig, grid = get_fig_grid()
    cmap = "YlOrRd"
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
            cmap=cmap,
        )
        add_subplot_label(fig, grid[i], i)
        if i == 1:
            add_scalebar(grid[i])

    add_colorbar(grid[-1], vmax=vmax, label="Importance", cmap=cmap)
    save_fig(fig, "demographics_importance", save_dir, extension)


def fig_density(
    lad20cd: str,
    oa: gpd.GeoDataFrame,
    all_groups: dict,
    save_dir: Path,
    extension: str,
    vmax: float = 6,
):
    """Save a figure showing the density of each demographic variable/objective for each
    output area (OA), measured as the fraction of the population in that OA divided by
    the area of the OA. Name of figure: demographics_density.png

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    oa : gpd.GeoDataFrame
        Data frame with stats for each variable in each output area (e.g. from
        calc_oa_density)
    all_groups : dict
        Short name (keys) and long title (values) for each objective
    save_dir : Path
        Directory to save figure in
    extension : str
        Figure file format
    vmax : float, optional
        Max value for colour scale, by default 6
    """
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
        add_subplot_label(fig, grid[i], i)
        if i == 1:
            add_scalebar(grid[i])

    add_colorbar(grid[-1], vmax=vmax, label=r"Density [% / $\mathrm{km}^2$]")
    save_fig(fig, "demographics_density", save_dir, extension)


def main():
    """Save figures showing the distribution of differrent sub-populations around the
    local authority.
    """
    print("Saving demographic figures...")
    set_fig_style()

    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    figs_dir, extension = get_figures_params(config)

    theta, _ = get_default_optimisation_params(config)
    population_groups, all_groups = get_objectives(config)

    oa_weights = get_weights(lad20cd, population_groups)
    fig_importance(lad20cd, all_groups, oa_weights, theta, figs_dir, extension)
    oa = calc_oa_density(lad20cd, all_groups, population_groups)
    fig_density(lad20cd, oa, all_groups, figs_dir, extension)


if __name__ == "__main__":
    main()
