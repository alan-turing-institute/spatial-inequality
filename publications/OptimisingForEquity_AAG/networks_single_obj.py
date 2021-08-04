from pathlib import Path
import pickle
from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import optimise
from utils import (
    get_config,
    get_objectives,
    get_all_optimisation_params,
    get_networks_save_dir,
)


def get_single_obj_filepath(config):
    networks_dir = get_networks_save_dir(config)
    filename = config["optimisation"]["single_objective"]["filename"]
    return Path(networks_dir, filename)


def make_single_obj_networks(lad20cd, population_groups, thetas, n_sensors, results={}):
    for name, weights in population_groups.items():
        if name not in results.keys():
            results[name] = {}

        for theta in thetas:
            if f"theta{theta}" not in results[name].keys():
                results[name][f"theta{theta}"] = {}

            for n in n_sensors:
                print("=" * 20)
                print(name, ", theta", theta, ", n_sensors", n)
                print("=" * 20)
                result = optimise(
                    lad20cd=lad20cd,
                    n_sensors=n,
                    theta=theta,
                    population_weight=1,
                    workplace_weight=0,
                    pop_age_groups={name: weights},
                )
                results[name][f"theta{theta}"][f"{n}sensors"] = result

    name = "workplace"
    if name not in results.keys():
        results[name] = {}
    for theta in thetas:
        if f"theta{theta}" not in results[name].keys():
            results[name][f"theta{theta}"] = {}

        for n in n_sensors:
            print("=" * 20)
            print(name, ", theta", theta, ", n_sensors", n)
            print("=" * 20)
            result = optimise(
                lad20cd=lad20cd,
                n_sensors=n,
                theta=theta,
                population_weight=0,
                workplace_weight=1,
            )
            results[name][f"theta{theta}"][f"{n}sensors"] = result

    return results


def main():
    config = get_config()
    lad20cd = lad20nm_to_lad20cd(config["la"])
    save_path = get_single_obj_filepath(config)
    population_groups, _ = get_objectives(config)
    thetas, n_sensors = get_all_optimisation_params(config)

    results = make_single_obj_networks(lad20cd, population_groups, thetas, n_sensors)
    with open(save_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
