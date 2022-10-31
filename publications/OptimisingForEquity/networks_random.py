from pathlib import Path

from utils import (
    get_all_optimisation_params,
    get_config,
    get_networks_save_dir,
    get_objectives,
    save_jsonpickle,
)

from spineq.data.census import PopulationDataset, WorkplaceDataset
from spineq.data.group import LocalAuthority
from spineq.mappings import lad20nm_to_lad20cd
from spineq.opt.coverage import ExponentialCoverage
from spineq.opt.objectives import Column, Objectives
from spineq.opt.random import Random


def get_random_filepath(config: dict) -> Path:
    """Get file path to save or load random networks.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config

    Returns
    -------
    Path
        Path to save optimised networks to
    """
    networks_dir = get_networks_save_dir(config)
    filename = config["optimisation"]["random"]["filename"]
    return Path(networks_dir, filename)


def make_random_networks(
    lad20cd: str,
    population_groups: dict,
    thetas: list,
    n_sensors: list,
    n_networks: int,
    results: dict = None,
) -> dict:
    """Generate networks optimised for a single objective (all age groups defined in
    `population_groups` and place of work), for a range of theta values
    (coverage distances) and numbers of sensors. Networks are generated with a greedy
    algorithm.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    population_groups : dict
        Parameters for residential population objectives, as returned by
        utils.get_objectives()
    thetas : list
        Theta (coverage distance) values to generate networks for
    n_sensors : list
        Generate networks with this many sensors
    results : dict, optional
        Previously generated results or metadata to add new networks to, by default {}

    Returns
    -------
    dict
        Optimised networks and coverage scores
    """
    if results is None:
        results = {}

    datasets = []
    columns = []
    for name, params in population_groups.items():
        datasets.append(
            PopulationDataset(lad20cd)
            .filter_age(low=params["min"], high=params["max"], name=name)
            .to_total()
        )
        columns.append(Column(name, "total"))
    name = "workplace"
    datasets.append(WorkplaceDataset(lad20cd, name=name))
    columns.append(Column(name, "workers"))

    randopt = Random(n_networks)

    la = LocalAuthority(lad20cd, datasets)

    for theta in thetas:
        if f"theta{theta}" not in results.keys():
            results[f"theta{theta}"] = {}

        cov = ExponentialCoverage.from_la(la, theta)
        objs = Objectives(la, columns, cov)

        for ns in n_sensors:
            print("theta", theta, ", n_sensors", ns)
            results[f"theta{theta}"][f"{ns}sensors"] = randopt.run(objs, ns)

    return results


def main():
    """
    Generate multi-objective networks for a local authority and save them to the path
    specified in config.yml.
    """
    print("Generating random networks...")
    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    save_path = get_random_filepath(config)
    population_groups, _ = get_objectives(config)
    thetas, n_sensors = get_all_optimisation_params(config)
    n_networks = config["optimisation"]["random"]["n"]
    results = make_random_networks(
        lad20cd, population_groups, thetas, n_sensors, n_networks
    )
    save_jsonpickle(results, save_path)


if __name__ == "__main__":
    main()
