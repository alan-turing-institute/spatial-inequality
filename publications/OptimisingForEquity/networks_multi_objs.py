import pickle
from pathlib import Path

import pygmo as pg
from utils import (
    get_all_optimisation_params,
    get_config,
    get_networks_save_dir,
    get_objectives,
)

from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.genetic import build_problem, run_problem
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


def make_multi_obj_networks(
    lad20cd: str,
    population_groups: dict,
    thetas: list,
    n_sensors: list,
    gen: int,
    population_size: int,
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
            pop = run_problem(
                prob,
                uda=pg.nsga2(gen=gen),
                population_size=population_size,
                verbosity=1,
            )
            results[f"theta{t}"][f"{ns}sensors"] = pop

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
        lad20cd, population_groups, thetas, n_sensors, gen, population_size
    )
    with open(save_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
