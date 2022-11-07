from pathlib import Path

from utils import (
    add_subplot_label,
    get_config,
    get_default_optimisation_params,
    get_figures_params,
    get_objectives,
    set_fig_style,
)

from spineq.data.census import PopulationDataset, WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.mappings import lad20nm_to_lad20cd
from spineq.opt.coverage import ExponentialCoverage
from spineq.opt.objectives import Column, CombinedObjectives
from spineq.plot.plotting import (
    add_colorbar,
    add_scalebar,
    get_fig_grid,
    plot_oa_importance,
    plot_oa_weights,
    save_fig,
)


def make_objs(lad20cd: str, population_groups: dict, theta: float) -> dict:
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

    la = LocalAuthority(lad20cd)
    for name, params in population_groups.items():
        la.add_dataset(
            PopulationDataset(lad20cd)
            .filter_age(low=params["min"], high=params["max"], name=name)
            .to_total()
        )
    la.add_dataset(WorkplaceDataset(lad20cd))
    cov = ExponentialCoverage.from_la(la, theta)

    objs = {
        name: CombinedObjectives(la, [Column(name, "total")], cov)
        for name in population_groups
    }
    name = "workplace"
    objs[name] = CombinedObjectives(la, [Column(name, "total")], cov)

    return objs


def fig_importance(
    groups: dict,
    objectives: dict,
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
    groups : dict
        Name and title of each population group/objective
    objectives : dict
        Objectives instance for each output area for each group/objective
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
            objectives[name],
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
    groups: dict,
    objectives: dict,
    save_dir: Path,
    extension: str,
    vmax: float = 6,
):
    """Save a figure showing the density of each demographic variable/objective for each
    output area (OA), measured as the fraction of the population in that OA divided by
    the area of the OA. Name of figure: demographics_density.png

    Parameters
    ----------
    groups : dict
        Short name (keys) and long title (values) for each objective
    objectives: dict
        CombinedObjectives instance for each objective in groups
    save_dir : Path
        Directory to save figure in
    extension : str
        Figure file format
    vmax : float, optional
        Max value for colour scale, by default 6
    """
    fig, grid = get_fig_grid()

    for i, g in enumerate(groups.items()):
        name = g[0]
        title = g[1]["title"]
        plot_oa_weights(
            objectives[name],
            density=True,
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

    objectives = make_objs(lad20cd, population_groups, theta)
    fig_importance(all_groups, objectives, figs_dir, extension)
    fig_density(all_groups, all_groups, figs_dir, extension)


if __name__ == "__main__":
    main()
