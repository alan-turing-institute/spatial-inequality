import os
from pathlib import Path
import pickle
from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import optimise
from utils import get_config


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
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_dir = config["optimisation"]["networks_dir"]
    filename = config["optimisation"]["single_objective"]["filename"]
    save_path = Path(save_dir, lad20cd, networks_dir, filename)
    os.makedirs(save_path.parent, exist_ok=True)

    population_groups = config["objectives"]["population_groups"]
    thetas = config["optimisation"]["theta"]["generate"]
    n_sensors = config["optimisation"]["n_sensors"]["generate"]

    results = make_single_obj_networks(lad20cd, population_groups, thetas, n_sensors)
    with open(save_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
