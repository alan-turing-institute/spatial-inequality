from pathlib import Path
from typing import List

import pygmo as pg
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
from spineq.opt.pygmo import PyGMO


def get_two_objs_filepath(config: dict) -> Path:
    """Get file path to save or load two-objective networks.

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
    filename = config["optimisation"]["two_objectives"]["filename"]
    return Path(networks_dir, filename)


def get_two_obj_inputs(
    lad20cd: str,
    objectives: list,
    population_groups: dict,
    workplace_name: str = "workplace",
) -> dict:
    """Get the inputs needed for the two-objective optimisation - the weights and
    location of each output area.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    objectives : str
        Names of the two objectives to include. Must be length two and names must match
        an entry in `population_groups` or `workplace_name`
    population_groups : dict
        Parameters for residential population objectives, as returned by
        utils.get_objectives
    workplace_name: str, optional
        Name of the place of work objective, by default "workplace"
    Returns
    -------
    dict
        Output area centroids and weights for each output area for each objective, as
        calculated by spineq.opt.optimise.get_optimisation_inputs
    """
    if len(objectives) != 2:
        raise ValueError(f"Must define 2 objectives in config.yml. Got {objectives}")

    datasets = []
    columns = []
    for obj in objectives:
        if obj == workplace_name:
            datasets.append(WorkplaceDataset(lad20cd, name=workplace_name))
            columns.append(Column(workplace_name, "workers"))
        else:
            datasets.append(
                PopulationDataset(lad20cd)
                .filter_age(
                    low=population_groups[obj]["min"],
                    high=population_groups[obj]["max"],
                    name=obj,
                )
                .to_total()
            )
            columns.append(Column(obj, "total"))

    return LocalAuthority(lad20cd, datasets), columns


def make_two_obj_networks(
    la: LocalAuthority,
    columns: List[Column],
    thetas: list,
    n_sensors: list,
    gen: int,
    population_size: int,
) -> dict:
    """Generate networks optimised for two objectives for a range of theta values
    (coverage distances) and numbers of sensors. Networks are generated with the
    NSGA2 algorithm.

    Parameters
    ----------
    la : LocalAuthority
        Local authority datasets for the LA to generate networks for
    columns : List[Column]
        Columns (in la.datasets) to create objectives from
    thetas : list
        Theta (coverage distance) values to generate networks for
    n_sensors : list
        Generate networks with this many sensors
    gen : int
        Number of generations (iterations) to run the optimisation for
    population_size : int
        Number of candidate networks in each generation

    Returns
    -------
    dict
        Optimised networks and coverage scores
    """
    opt = PyGMO(pg.nsga2(gen=gen), population_size)
    results = {}
    for t in thetas:
        results[f"theta{t}"] = {}
        cov = ExponentialCoverage.from_la(la, t)
        objs = Objectives(la, columns, cov)
        for ns in n_sensors:
            print("theta", t, ", n_sensors", ns)
            result = opt.run(objs, ns)
            results[f"theta{t}"][f"{ns}sensors"] = result

    return results


def main():
    """
    Generate two-objective networks for a local authority and save them to the path
    specified in config.yml.
    """
    print("Generating two-objective networks...")
    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    save_path = get_two_objs_filepath(config)

    population_groups, _ = get_objectives(config)
    thetas, n_sensors = get_all_optimisation_params(config)
    gen = config["optimisation"]["two_objectives"]["gen"]
    population_size = config["optimisation"]["two_objectives"]["population_size"]
    seed = config["optimisation"]["two_objectives"]["seed"]
    pg.set_global_rng_seed(seed=seed)
    objectives = config["optimisation"]["two_objectives"]["objectives"]
    la, columns = get_two_obj_inputs(lad20cd, objectives, population_groups)

    results = make_two_obj_networks(
        la, columns, thetas, n_sensors, gen, population_size
    )
    save_jsonpickle(results, save_path)


if __name__ == "__main__":
    main()
