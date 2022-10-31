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
from spineq.opt.greedy import Greedy
from spineq.opt.objectives import Column, CombinedObjectives


def get_single_obj_filepath(config: dict) -> Path:
    """Get file path to save or load single objective networks.

    Parameters
    ----------
    config : dict
        Parameters as loaded by utils.get_config()

    Returns
    -------
    Path
        Path to save optimised networks to
    """
    networks_dir = get_networks_save_dir(config)
    filename = config["optimisation"]["single_objective"]["filename"]
    return Path(networks_dir, filename)


def make_single_obj_networks(
    lad20cd: str,
    population_groups: dict,
    thetas: list,
    n_sensors: list,
    results: dict = {},
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
    greedy = Greedy()

    for name, params in population_groups.items():
        if name not in results.keys():
            results[name] = {}

        la = LocalAuthority(
            lad20cd,
            [
                PopulationDataset(lad20cd)
                .filter_age(low=params["min"], high=params["max"], name=name)
                .to_total()
            ],
        )

        for theta in thetas:
            if f"theta{theta}" not in results[name].keys():
                results[name][f"theta{theta}"] = {}

            cov = ExponentialCoverage.from_la(la, theta)
            objs = CombinedObjectives(la, [Column(name, "total")], cov)

            for n in n_sensors:
                print("=" * 20)
                print(name, ", theta", theta, ", n_sensors", n)
                print("=" * 20)
                result = greedy.run(objs, n)
                results[name][f"theta{theta}"][f"{n}sensors"] = result

    name = "workplace"
    la = LocalAuthority(lad20cd, [WorkplaceDataset(lad20cd, name=name)])
    if name not in results.keys():
        results[name] = {}
    for theta in thetas:
        if f"theta{theta}" not in results[name].keys():
            results[name][f"theta{theta}"] = {}

        cov = ExponentialCoverage.from_la(la, theta)
        objs = CombinedObjectives(la, [Column(name, "total")], cov)

        for n in n_sensors:
            print("=" * 20)
            print(name, ", theta", theta, ", n_sensors", n)
            print("=" * 20)
            result = greedy.run(objs, n)
            results[name][f"theta{theta}"][f"{n}sensors"] = result

    return results


def main():
    """
    Generate single objective networks for a local authority and save them to the path
    specified in config.yml.
    """
    print("Generating single objective networks...")
    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    save_path = get_single_obj_filepath(config)
    population_groups, _ = get_objectives(config)
    thetas, n_sensors = get_all_optimisation_params(config)

    results = make_single_obj_networks(lad20cd, population_groups, thetas, n_sensors)
    save_jsonpickle(results, save_path)


if __name__ == "__main__":
    main()
