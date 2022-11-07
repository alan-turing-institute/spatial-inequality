from pathlib import Path
from typing import Union

import numpy as np
import pygmo as pg
from tqdm import trange
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
from spineq.opt.pygmo import PyGMO, PyGMOResult


def get_multi_objs_filepath(config: dict) -> Path:
    """Get file path to save or load multi-objective networks.

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
    filename = config["optimisation"]["multi_objectives"]["filename"]
    return Path(networks_dir, filename)


def get_multi_obj_inputs(lad20cd: str, population_groups: dict) -> dict:
    """Get the inputs needed for the multi-objective optimisation - the weights and
    location of each output area.

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
        Output area centroids and weights for each output area for each objective, as
        calculated by spineq.opt.optimise.get_optimisation_inputs
    """
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
    return LocalAuthority(lad20cd, datasets), columns


class Log:
    def __init__(self):
        self.generations = []
        self.fitness = []
        self.hypervolume = []
        self.scores = []
        self.sensors = []

    def log(self, result: PyGMOResult, generations: int):
        self.generations.append(generations)
        self.scores.append(result.total_coverage)
        self.sensors.append(result.population)
        self.fitness.append(result.best_coverage())
        hv = pg.hypervolume(-result.total_coverage).compute(
            np.zeros(result.objectives.n_obj)
        )
        self.hypervolume.append(hv)


def run_nsga_with_log(
    objs, n_sensors, gen=100, population_size=100, log_every=100, save_path=None
):
    opt = PyGMO(pg.nsga2(gen=log_every), population_size)

    # solve problem
    log = Log()
    result = None
    for g in trange(log_every, gen + log_every, log_every):
        result = opt.update(result) if result else opt.run(objs, n_sensors)
        log.log(result, g)
        if save_path:
            save_jsonpickle(log.__dict__, save_path)

    return result, log


def make_multi_obj_networks(
    lad20cd: str,
    population_groups: dict,
    thetas: list,
    n_sensors: list,
    gen: int,
    population_size: int,
    save_path: Union[str, Path, None] = None,
) -> dict:
    """Generate networks optimised for multiple objectives (all age groups defined in
    `population_groups` and place of work), for a range of theta values
    (coverage distances) and numbers of sensors. Networks are generated with the
    NSGA2 algorithm.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    population_groups : dict
        Parameters for residential population objectives, as returned by
        utils.get_objectives
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
    la, columns = get_multi_obj_inputs(lad20cd, population_groups)

    results = {}
    for t in thetas:
        results[f"theta{t}"] = {}
        cov = ExponentialCoverage.from_la(la, t)
        objs = Objectives(la, columns, cov)
        for ns in n_sensors:
            print("theta", t, ", n_sensors", ns)
            result, log = run_nsga_with_log(
                objs,
                ns,
                gen=gen,
                population_size=population_size,
                log_every=100,
                save_path=f"{save_path}_theta{t}_{ns}sensors.log",
            )
            results[f"theta{t}"][f"{ns}sensors"] = {
                "result": result,
                "log": log.__dict__,
            }

    return results


def main():
    """
    Generate multi-objective networks for a local authority and save them to the path
    specified in config.yml.
    """
    print("Generating multi-objective networks...")
    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    save_path = get_multi_objs_filepath(config)

    population_groups, _ = get_objectives(config)
    thetas, n_sensors = get_all_optimisation_params(config)
    gen = config["optimisation"]["multi_objectives"]["gen"]
    population_size = config["optimisation"]["multi_objectives"]["population_size"]
    seed = config["optimisation"]["multi_objectives"]["seed"]
    pg.set_global_rng_seed(seed=seed)

    results = make_multi_obj_networks(
        lad20cd,
        population_groups,
        thetas,
        n_sensors,
        gen,
        population_size,
        save_path=save_path,
    )
    save_jsonpickle(results, save_path)


if __name__ == "__main__":
    main()
