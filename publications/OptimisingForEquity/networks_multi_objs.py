import pickle
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
)

from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.genetic import build_problem, run_problem, extract_all
from spineq.optimise import get_optimisation_inputs


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
        calculated by spineq.optimise.get_optimisation_inputs
    """
    return get_optimisation_inputs(
        lad20cd=lad20cd,
        population_weight=1,
        workplace_weight=1,
        pop_age_groups=population_groups,
        combine=False,
    )


class Log:
    def __init__(self):
        self.generations = []
        self.fitness = []
        self.hypervolume = []
        self.scores = []
        self.sensors = []

    def log(self, pop, generations):
        self.generations.append(generations)
        scores, sensors = extract_all(pop)
        self.scores.append(scores)
        self.sensors.append(sensors)
        self.fitness.append(scores.min(axis=0))
        hv = pg.hypervolume(scores).compute(np.zeros(scores.shape[1]))
        self.hypervolume.append(hv)


def run_nsga_with_log(
    prob, gen=100, population_size=100, log_every=100, save_path=None
):
    # Create algorithm to solve problem with
    uda = pg.nsga2(gen=log_every)
    algo = pg.algorithm(uda=uda)

    # population for problem
    pop = pg.population(prob=prob, size=population_size)

    # solve problem
    log = Log()
    for g in trange(log_every, gen + log_every, log_every):
        pop = algo.evolve(pop)
        log.log(pop, g)
        if save_path:
            with open(f"{save_path}.log", "wb") as f:
                pickle.dump(log.__dict__, f)

    return pop, log


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
    inputs = get_multi_obj_inputs(lad20cd, population_groups)

    results = {}
    for t in thetas:
        results[f"theta{t}"] = {}
        for ns in n_sensors:
            print("theta", t, ", n_sensors", ns)
            prob = build_problem(inputs, n_sensors=ns, theta=t)
            """
            pop, log = run_nsga_with_log(
                prob,
                gen=gen,
                population_size=population_size,
                log_every=100,
                save_path=f"{save_path}_theta{t}_{ns}sensors",
            )
            results[f"theta{t}"][f"{ns}sensors"] = {"pop": pop, "log": log.__dict__}
            """
            pop, algo = run_problem(
                prob,
                uda=pg.nsga2(gen=gen),
                population_size=population_size,
            )
            log = algo.extract(pg.nsga2).get_log()
            results[f"theta{t}"][f"{ns}sensors"] = {"pop": pop, "log": log}
            with open(f"{save_path}_theta{t}_{ns}sensors.log", "wb") as f:
                pickle.dump(log, f)

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
    with open(save_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
