from pathlib import Path

import numpy as np
from tqdm import trange
from utils import (
    get_all_optimisation_params,
    get_config,
    get_networks_save_dir,
    get_objectives,
    save_jsonpickle,
)

from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import calc_coverage, get_optimisation_inputs


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

    oa_weight = get_optimisation_inputs(
        population_weight=1,
        workplace_weight=1,
        pop_age_groups=population_groups,
        combine=False,
    )
    for theta in thetas:
        if f"theta{theta}" not in results.keys():
            results[f"theta{theta}"] = {}

        for ns in n_sensors:
            print("theta", theta, ", n_sensors", ns)
            rnd_oa = np.random.choice(oa_weight["oa11cd"], size=(n_networks, ns))
            rnd_scores = np.array(
                [
                    [
                        calc_coverage(lad20cd, rnd_oa[i, :], oa_weight=w, theta=theta)[
                            "total_coverage"
                        ]
                        for w in oa_weight["oa_weight"].values()
                    ]
                    for i in trange(rnd_oa.shape[0])
                ]
            )
            results[f"theta{theta}"][f"{ns}sensors"] = rnd_scores

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
