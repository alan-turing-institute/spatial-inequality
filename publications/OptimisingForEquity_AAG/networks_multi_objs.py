import os
from pathlib import Path
import pickle
import pygmo as pg
from utils import get_config
from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import get_optimisation_inputs
from spineq.genetic import build_problem, run_problem


def get_multi_obj_inputs(lad20cd, population_groups):
    return get_optimisation_inputs(
        lad20cd=lad20cd,
        population_weight=1,
        workplace_weight=1,
        pop_age_groups=population_groups,
        combine=False,
    )


def make_multi_obj_networks(
    lad20cd, population_groups, thetas, n_sensors, gen, population_size
):
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
    config = get_config()
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_dir = config["optimisation"]["networks_dir"]
    filename = config["optimisation"]["multi_objectives"]["filename"]
    save_path = Path(save_dir, lad20cd, networks_dir, filename)
    os.makedirs(save_path.parent, exist_ok=True)

    population_groups = config["objectives"]["population_groups"]
    thetas = config["optimisation"]["theta"]["generate"]
    n_sensors = config["optimisation"]["n_sensors"]["generate"]
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
