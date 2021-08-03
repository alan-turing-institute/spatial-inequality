import os
from pathlib import Path
import pickle
import pygmo as pg
from config import config
from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import get_optimisation_inputs
from spineq.genetic import build_problem, run_problem


def get_two_obj_inputs(
    lad20cd, objectives, population_groups, workplace_name="workplace"
):
    if len(objectives) != 2:
        raise ValueError(f"Must define 2 objectives in config.yml. Got {objectives}")

    workplace_weight = 1 if workplace_name in objectives else 0
    return get_optimisation_inputs(
        lad20cd=lad20cd,
        population_weight=1,
        workplace_weight=workplace_weight,
        pop_age_groups={
            obj: population_groups[obj] for obj in objectives if obj != workplace_name
        },
        combine=False,
    )


def make_two_obj_networks(inputs, thetas, n_sensors, gen, population_size):
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
    save_dir = config["save_dir"]
    lad20cd = lad20nm_to_lad20cd(config["la"])
    networks_dir = config["optimisation"]["networks_dir"]
    filename = config["optimisation"]["two_objectives"]["filename"]
    save_path = Path(save_dir, lad20cd, networks_dir, filename)
    os.makedirs(save_path.parent, exist_ok=True)

    population_groups = config["objectives"]["population_groups"]
    thetas = config["optimisation"]["theta"]["generate"]
    n_sensors = config["optimisation"]["n_sensors"]["generate"]
    gen = config["optimisation"]["two_objectives"]["gen"]
    population_size = config["optimisation"]["two_objectives"]["population_size"]
    seed = config["optimisation"]["two_objectives"]["seed"]
    pg.set_global_rng_seed(seed=seed)
    objectives = config["optimisation"]["two_objectives"]["objectives"]
    inputs = get_two_obj_inputs(lad20cd, objectives, population_groups)

    results = make_two_obj_networks(inputs, thetas, n_sensors, gen, population_size)
    with open(save_path, "wb") as f:
        pickle.dump(results, f)


if __name__ == "__main__":
    main()
