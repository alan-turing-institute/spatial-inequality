from datetime import datetime
import json
import os
from pathlib import Path
import pickle
from tqdm import tqdm
import pygmo as pg

from spineq.data_fetcher import lad20nm_to_lad20cd
from spineq.optimise import get_optimisation_inputs
from spineq.genetic import build_problem, run_problem


def get_multi_obj_inputs(
    lad20cd: str,
    objectives: list,
    population_groups: dict,
    workplace_name: str = "workplace",
) -> dict:
    """Get the inputs needed for the multi-objective optimisation - the weights and
    location of each output area for each of the specified objectives.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    objectives : list
        Names of the two objectives to include. Must be length two and names must match
        an entry in `population_groups` or `workplace_name`
    population_groups : dict
        Parameters for residential population objectives
    workplace_name: str, optional
        Name of the place of work objective, by default "workplace"
    Returns
    -------
    dict
        Output area centroids and weights for each output area for each objective, as
        calculated by spineq.optimise.get_optimisation_inputs
    """
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


def make_multi_obj_networks(
    lad20cd: str,
    population_groups: dict,
    objectives: list,
    thetas: list,
    n_sensors: list,
    gen: int,
    population_size: int,
    save_path: Path,
    workplace_name: str = "workplace",
):
    """Generate networks optimised for multiple objectives (all age groups defined in
    `population_groups` and place of work), for a range of theta values
    (coverage distances) and numbers of sensors. Networks are generated with the
    NSGA2 algorithm.

    Parameters
    ----------
    lad20cd : str
        Local authority code to generate results for
    population_groups : dict
        Parameters for residential population objectives
    objectives : list
        Names of the two objectives to include. Must be length two and names must match
        an entry in `population_groups` or `workplace_name`
    thetas : list
        Theta (coverage distance) values to generate networks for
    n_sensors : list
        Generate networks with this many sensors
    gen : int
        Number of generations (iterations) to run the optimisation for
    population_size : int
        Number of candidate networks in each generation
    save_path : Path
        Where to save networks
    workplace_name: str, optional
        Name of the place of work objective, by default "workplace"
    """
    inputs = [
        get_multi_obj_inputs(
            lad20cd,
            obj,
            population_groups,
            workplace_name,
        )
        for obj in objectives
    ]

    for inp in tqdm(inputs, desc="objectives"):
        for t in tqdm(thetas, desc="theta"):
            for ns in tqdm(n_sensors, desc="n_sensors"):
                prob = build_problem(inp, n_sensors=ns, theta=t)
                pop = run_problem(
                    prob,
                    uda=pg.nsga2(gen=gen),
                    population_size=population_size,
                    verbosity=0,
                )
                net_path = Path(save_path, f"theta_{t}_nsensors_{ns}.pkl")
                with open(net_path, "wb") as f:
                    pickle.dump({"objectives": objectives, "population": pop}, f)


def main():
    """
    Generate multi-objective networks for a local authority for a range of theta values,
    numbers of sensors, and objectives.
    """
    print("Generating multi-objective networks...")
    la = "Newcastle upon Tyne"
    thetas = [500]
    n_sensors = [55]
    gen = 1000
    population_size = 200
    seed = 123
    population_groups = {
        "pop_total": {
            "min": 0,
            "max": 90,
            "weight": 1,
            "title": "Total Residents",
        },
        "pop_children": {
            "min": 0,
            "max": 15,
            "weight": 1,
            "title": "Residents Under 16",
        },
        "pop_elderly": {
            "min": 66,
            "max": 90,
            "weight": 1,
            "title": "Residents Over 65",
        },
    }
    workplace_name = "workplace"
    objectives = [
        ["workplace", "pop_elderly", "pop_children", "pop_total"],
        ["workplace", "pop_elderly", "pop_children"],
        ["workplace", "pop_elderly"],
        ["workplace"],
    ]

    lad20cd = lad20nm_to_lad20cd(la)
    pg.set_global_rng_seed(seed=seed)
    save_path = Path(f"data/networks/{datetime.now().strftime('%Y-%m-%d_%H%M%S')}")
    os.makedirs(save_path)

    with open(Path(save_path, "meta.json"), "w") as f:
        json.dump(
            {
                "la": la,
                "lad20cd": lad20cd,
                "thetas": thetas,
                "n_sensors": n_sensors,
                "gen": gen,
                "population_size": population_size,
                "seed": seed,
                "population_groups": population_groups,
                "objectives": objectives,
            },
            f,
            indent=4,
        )

    make_multi_obj_networks(
        lad20cd,
        population_groups,
        objectives,
        thetas,
        n_sensors,
        gen,
        population_size,
        save_path,
        workplace_name=workplace_name,
    )


if __name__ == "__main__":
    main()
