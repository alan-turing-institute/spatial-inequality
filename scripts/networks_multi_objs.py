import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pygmo as pg
from tqdm import tqdm

from publications.OptimisingForEquity.utils import save_jsonpickle
from spineq.data.fetcher import lad20nm_to_lad20cd
from spineq.opt.genetic import build_problem, extract_all, run_problem
from spineq.opt.optimise import calc_coverage, get_optimisation_inputs


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
        Names of the two objectives to include. Must have at least two elements and
        names must match an entry in `population_groups` or `workplace_name`
    population_groups : dict
        Parameters for residential population objectives
    workplace_name: str, optional
        Name of the place of work objective, by default "workplace"
    Returns
    -------
    dict
        Output area centroids and weights for each output area for each objective, as
        calculated by spineq.opt.optimise.get_optimisation_inputs
    """
    if len(objectives) < 2:
        raise ValueError(
            "At least two objectives must be defined "
            f"len(objectives) = {len(objectives)}))"
        )
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


def get_pop_oa_coverage(
    sensor_ids: np.ndarray, opt_inputs: dict, lad20cd: str, theta: float
) -> np.ndarray:
    """[summary]

    Parameters
    ----------
    sensor_ids : np.ndarray
        Sensor output area IDs for each sensor in each network (the IDs can be used to
        retrieve an output area code from opt_inputs['oa11cd']). Shape
        (n_networks, n_sensors).
    opt_inputs : dict
        Optimisation inputs as calculated by spineq.optimiise.get_optimisation_inputs
    lad20cd : str
        Local authtority code
    theta : float
        Coverage decay distance used for generating the networks and coverage values

    Returns
    -------
    np.ndarray
        Coverage of each output area in each network, shape (n_networks, n_output_areas)
    """
    n_networks = sensor_ids.shape[0]
    n_oa = len(opt_inputs["oa11cd"])
    oa_coverage = np.zeros((n_networks, n_oa))
    for idx_network in range(n_networks):
        sensor_dict = [
            {
                "oa11cd": opt_inputs["oa11cd"][idx_sensor],
                "x": opt_inputs["oa_x"][idx_sensor],
                "y": opt_inputs["oa_y"][idx_sensor],
            }
            for idx_sensor in sensor_ids[idx_network, :].astype(int)
        ]
        net_coverage = calc_coverage(lad20cd, sensor_dict, oa_weight=1, theta=theta)
        oa_coverage[idx_network, :] = [
            oa["coverage"] for oa in net_coverage["oa_coverage"]
        ]
    return oa_coverage


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
    include_oa_coverage: bool = True,
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

    for inp_idx, inp in enumerate(tqdm(inputs, desc="objectives")):
        for t in tqdm(thetas, desc="theta"):
            for ns in tqdm(n_sensors, desc="n_sensors"):
                prob = build_problem(inp, n_sensors=ns, theta=t)
                pop = run_problem(
                    prob,
                    uda=pg.nsga2(gen=gen),
                    population_size=population_size,
                    verbosity=0,
                )
                net_name = f"theta_{t}_nsensors_{ns}_objs_{inp_idx}"
                net_path = Path(save_path, f"{net_name}.pkl")
                save_jsonpickle(
                    {
                        "lad20cd": lad20cd,
                        "objectives": list(inp["oa_weight"].keys()),
                        "theta": t,
                        "n_sensors": ns,
                        "population": pop,
                    },
                    net_path,
                )
                scores, solutions = extract_all(pop)
                scores = -scores
                if include_oa_coverage:
                    oa_coverage = get_pop_oa_coverage(solutions, inp, lad20cd, t)
                else:
                    oa_coverage = np.array([])
                net_path = Path(save_path, f"{net_name}.json")
                with open(net_path, "w") as f:
                    json.dump(
                        {
                            "lad20cd": lad20cd,
                            "objectives": list(inp["oa_weight"].keys()),
                            "theta": t,
                            "n_sensors": ns,
                            "oa11cd": inp["oa11cd"].tolist(),
                            "sensors": solutions.astype(int).tolist(),
                            "obj_coverage": scores.tolist(),
                            "oa_coverage": oa_coverage.tolist(),
                        },
                        f,
                    )


def main():
    """
    Generate multi-objective networks for a local authority for a range of theta values,
    numbers of sensors, and objectives. Save them in pkl and json format, as well as
    meta data.
    """
    print("Generating multi-objective networks...")
    la = "Gateshead"
    thetas = [500]  # [100, 250, 500]
    n_sensors = [10]  # [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    gen = 2  # 1000
    population_size = 8  # 200
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
    ]
    include_oa_coverage = True

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
                "workplace_name": workplace_name,
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
        include_oa_coverage=include_oa_coverage,
    )


if __name__ == "__main__":
    main()
