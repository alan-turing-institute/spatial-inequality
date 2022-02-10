"""Main optimisation functions.
"""
import datetime
import json
import os

import numpy as np
import pandas as pd
import rq
from flask_socketio import SocketIO

from spineq.data_fetcher import get_oa_centroids, get_oa_stats
from spineq.greedy import greedy_opt
from spineq.utils import coverage_matrix, make_job_dict, total_coverage


def optimise(
    lad20cd="E08000021",
    n_sensors=20,
    theta=500,
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    rq_job=False,
    socket=False,
    redis_url="redis://",
    save_result=False,
    save_plot=False,
    save_dir="",
    run_name="",
    **kwargs
):
    """Greedily place sensors to maximise coverage.

    Keyword Arguments:
        lad20cd {str} -- 2020 local authority district code to get output areas for (
        default E08000021, which is Newcastle upon Tyne)

        n_sensors {int} -- number of sensors to place (default: {20})
        theta {float} -- coverage decay rate (default: {500})

        population_weight, workplace_weight, pop_age_groups -- As defined in
        calc_oa_weights (parameters directly passed to that function.)
        (all passed to cala_oa_weights)

        rq_job {boolean} -- If True attempt to get the RQ job running this
        function and upate meta data with progress.
        socket {boolean} -- If True attempt to make a SocketIO connection to
        send updates to.
        redis_url {str} -- URL of Redis server for SocketIO message queue
        (default: {"redis://"})

        save_result {boolean} -- If True save a json of optimisation results to
        file {save_dir}/{run_name}_result.json {default: {False}}
        save_plots {str} -- If 'final' save plot of final sensor network,
        if 'all' save plot after placing each sensor, if False save no plots.
        {default: {False}}
        save_dir {str} -- Directory to save plots in.
        Defaults to current directory. {default: {""}}
        run_name {str} -- Prefix to add to saved plots. If empty defaults to
        current date and time YYYYMMDDhhmm {default: {""}}
        **kwrargs -- additional arguments to pass to plotting function.

    Returns:
        dict -- optimisation result.
    """
    if rq_job or socket:
        print("Setting up jobs and sockets...")
    if rq_job:
        job = rq.get_current_job()
        print("rq_job", rq_job)
        print("job", job)
    else:
        job = None
    if socket:
        socketIO = SocketIO(message_queue=redis_url)
        print("socket", socket)
        print("socketIO", socketIO)
    else:
        socketIO = None

    print("Fetching data...")
    if job:
        job.meta["status"] = "Fetching data"
        job.save_meta()

    data = get_optimisation_inputs(
        lad20cd=lad20cd,
        population_weight=population_weight,
        workplace_weight=workplace_weight,
        pop_age_groups=pop_age_groups,
        combine=True,
    )
    oa_x = data["oa_x"]
    oa_y = data["oa_y"]
    oa_weight = data["oa_weight"]
    oa11cd = data["oa11cd"]

    # Compute coverage matrix: coverage at each OA due to a sensor placed at
    #  any other OA.
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    # Run the optimisation
    result = greedy_opt(
        n_sensors=n_sensors,
        coverage=coverage,
        weights=oa_weight,
        job=job,
        socketIO=socketIO,
    )

    result = make_result_dict(
        lad20cd,
        n_sensors,
        theta,
        oa_x,
        oa_y,
        oa11cd,
        result["sensors"],
        result["total_coverage"],
        result["point_coverage"],
        list(oa11cd[result["placement_history"]]),
        result["coverage_history"],
        oa_weight=result["weights"],
        pop_age_groups=pop_age_groups,
        population_weight=population_weight,
        workplace_weight=workplace_weight,
    )

    if job:
        job.meta["progress"] = 100
        job.meta["status"] = "Finished"
        job.save_meta()
        if socket:
            jobDict = make_job_dict(job)
            jobDict["result"] = result
            socketIO.emit("jobFinished", jobDict)

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    if not run_name:
        now = datetime.datetime.now()
        run_name = now.strftime("%Y%m%d%H%M")
    if save_plot:
        from .plotting import plot_optimisation_result

        save_path = "{}/{}_nsensors_{:03d}.png".format(save_dir, run_name, n_sensors)
        plot_optimisation_result(result, save_path=save_path, **kwargs)

    if save_result:
        result_file = "{}/{}_result.json".format(save_dir, run_name)
        with open(result_file, "w") as f:
            json.dump(result, f, indent=4)

    return result


def calc_oa_weights(
    lad20cd="E08000021",
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    combine=True,
):
    """Calculate weighting factor for each OA.

    Keyword Arguments:
        lad20cd {str} -- 2020 local authority district code to get output areas for (
        default E08000021, which is Newcastle upon Tyne)

        population_weight {float} -- Weighting for residential population
        (default: {1})

        workplace_weight {float} -- Weighting for workplace population
        (default: {0})

        pop_age_groups {dict} -- Residential population age groups to create
        objectives for and their corresponding weights. Dict with objective
        name as key. Each entry should be another dict with keys min (min age
        in population group), max (max age in group), and weight (objective
        weight for this group).

        combine {bool} -- If True combine all the objectives weights into a
        single overall weight using the defined weighting factors. If False
        treat all objectives separately, in which case all weights defined in
        other parameters are ignored.

    Returns:
        pd.DataFrame or pd.Series -- Weight for each OA (indexed by oa11cd) for
        each objective. Series if only one objective defined or combine is True.
    """

    data = get_oa_stats(lad20cd=lad20cd)
    population_ages = data["population_ages"]
    workplace = data["workplace"]

    if len(population_ages) != len(workplace):
        raise ValueError(
            "Lengths of inputs don't match: population_ages={}, workplace={}".format(
                len(population_ages), len(workplace)
            )
        )

    # weightings for residential population by age group
    if population_weight > 0:
        oa_population_group_weights = {}
        for name, group in pop_age_groups.items():
            # skip calculation for zeroed objectives
            if group["weight"] == 0:
                continue

            # get sum of population in group age range
            group_population = population_ages.loc[
                :,
                (population_ages.columns >= group["min"])
                & (population_ages.columns <= group["max"]),
            ].sum(axis=1)

            # normalise total population
            group_population = group_population / group_population.sum()

            # if objectives will be combined, scale by group weight
            if combine:
                group_population = group_population * group["weight"]

            oa_population_group_weights[name] = group_population

        if len(oa_population_group_weights) > 0:
            use_population = True  # some population groups with non-zero weights

            oa_population_group_weights = pd.DataFrame(oa_population_group_weights)
            if combine:
                oa_population_group_weights = oa_population_group_weights.sum(axis=1)
                oa_population_group_weights = population_weight * (
                    oa_population_group_weights / oa_population_group_weights.sum()
                )
        else:
            use_population = False  #  all population groups had zero weight
    else:
        use_population = False

    # weightings for number of workers in OA (normalised to sum to 1)
    if workplace_weight > 0:
        use_workplace = True
        workplace = workplace / workplace.sum()
        if combine:
            workplace = workplace_weight * workplace
        workplace.name = "workplace"
    else:
        use_workplace = False

    if not use_population and not use_workplace:
        raise ValueError("Must specify at least one non-zero weight.")

    if combine:
        if use_workplace and use_population:
            oa_all_weights = pd.DataFrame(
                {"workplace": workplace, "population": oa_population_group_weights}
            )
            oa_all_weights = oa_all_weights.sum(axis=1)
            return oa_all_weights / oa_all_weights.sum()
        elif use_workplace:
            return workplace
        elif use_population:
            return oa_population_group_weights
    else:
        if use_workplace and use_population:
            return oa_population_group_weights.join(workplace)
        elif use_workplace:
            return workplace
        elif use_population and len(oa_population_group_weights.columns) > 1:
            return oa_population_group_weights
        else:
            return oa_population_group_weights[oa_population_group_weights.columns[0]]


def get_optimisation_inputs(
    lad20cd="E08000021",
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    combine=True,
):
    """Get input data in format needed for optimisation.

    Keyword Arguments:
        lad20cd, population_weight, workplace_weight, pop_age_groups, combine -- As
        defined in calc_oa_weights (parameters directly passed to that
        function.)

    Returns:
        dict -- Optimisation input data
    """
    centroids = get_oa_centroids(lad20cd=lad20cd)
    weights = calc_oa_weights(
        lad20cd=lad20cd,
        population_weight=population_weight,
        workplace_weight=workplace_weight,
        pop_age_groups=pop_age_groups,
        combine=combine,
    )
    if type(weights) == pd.DataFrame:
        weights_columns = ["weight_" + name for name in weights.columns]
        weights.columns = weights_columns
    else:
        weights.name = "weights"

    if len(centroids) != len(weights):
        raise ValueError(
            "Lengths of inputs don't match: centroids={}, weights={}".format(
                len(centroids), len(weights)
            )
        )

    centroids = centroids.join(weights)

    oa11cd = centroids.index.values
    oa_x = centroids["x"].values
    oa_y = centroids["y"].values

    if type(weights) == pd.DataFrame:
        oa_weight = {
            name.replace("weight_", ""): centroids[name].values
            for name in weights_columns
        }
    else:
        oa_weight = centroids[weights.name].values

    return {"oa11cd": oa11cd, "oa_x": oa_x, "oa_y": oa_y, "oa_weight": oa_weight}


def make_result_dict(
    lad20cd,
    n_sensors,
    theta,
    oa_x,
    oa_y,
    oa11cd,
    sensors,
    total_coverage,
    oa_coverage,
    placement_history,
    coverage_history,
    oa_weight=None,
    pop_age_groups=None,
    population_weight=None,
    workplace_weight=None,
):
    """Package up optimisation parameters and results as a dictionary, which
    is used by the API and some other functions.

    Arguments:
        n_sensors {int} -- number of sensors
        theta {float} -- coverage decay parameter
        oa_x {list} -- x position of each OA
        oa_y {list} -- y position of each OA
        oa11cd {list} -- id of each OA
        sensors {list} -- 1 if OA has sensor, 0 otherwise
        total_coverage {float} -- total coverage metric for this network
        oa_coverage {list} -- coverage of each OA for this network

    Keyword Arguments:
        oa_weight {list} -- weight for each OA
        pop_age_groups {dict} -- population age groups (see calc_oa_weights)
        population_weight {float} -- Weighting for residential population
        workplace_weight {float} -- Weighting for workplace population

    Returns:
        dict -- Optimisation results and parameters. Keys: n_sensors, theta,
        pop_age_groups, population_weight, workplace_weight, sensors,
        total_coverage, oa_coverage
    """
    n_poi = len(oa_x)
    sensor_locations = [
        {"x": oa_x[i], "y": oa_y[i], "oa11cd": oa11cd[i]}
        for i in range(n_poi)
        if sensors[i] == 1
    ]

    oa_coverage = [
        {"oa11cd": oa11cd[i], "coverage": oa_coverage[i]} for i in range(n_poi)
    ]

    if oa_weight is not None:
        oa_weight = [
            {"oa11cd": oa11cd[i], "weight": oa_weight[i]} for i in range(n_poi)
        ]

    return {
        "lad20cd": lad20cd,
        "n_sensors": n_sensors,
        "theta": theta,
        "sensors": sensor_locations,
        "total_coverage": total_coverage,
        "oa_coverage": oa_coverage,
        "oa_weight": oa_weight,
        "placement_history": placement_history,
        "coverage_history": coverage_history,
        "pop_age_groups": pop_age_groups,
        "population_weight": population_weight,
        "workplace_weight": workplace_weight,
    }


def calc_coverage(lad20cd, sensors, oa_weight=None, theta=500):
    """Calculate the coverage of a network for arbitrary OA weightings.

    Arguments:
        sensors {list} -- List of OA (oa11cd) with a sensor.
        oa_weight {pd.Series} -- Weight for each OA, pandas series with index
        oa11cd and weights as values. If None weight all OA equally.

    Keyword Arguments:
        theta {int} -- coverage decay rate (default: {500})

    Returns:
        dict -- Coverage stats with keys "total_coverage" and "oa_coverage".
    """
    centroids = get_oa_centroids(lad20cd)

    oa_x = centroids["x"].values
    oa_y = centroids["y"].values
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    # only keep coverages due to sites where a sensor is present
    centroids["has_sensor"] = 0
    for oa in sensors:
        centroids.loc[oa, "has_sensor"] = 1
    sensors = centroids["has_sensor"].values
    mask_cov = np.multiply(coverage, sensors[np.newaxis, :])

    # coverage at each site = coverage due to nearest sensor
    oa_coverage = np.max(mask_cov, axis=1)

    # Avg coverage = weighted sum across all points of interest
    if oa_weight is None:
        oa_weight = 1  # equal weights for each OA
    elif isinstance(oa_weight, pd.DataFrame) and len(oa_weight.columns) == 1:
        oa_weight = oa_weight[oa_weight.columns[0]]

    if isinstance(oa_weight, pd.DataFrame):
        overall_coverage = {}
        for obj in oa_weight.columns:
            centroids["weight"] = oa_weight[obj]
            overall_coverage[obj] = total_coverage(
                oa_coverage, centroids["weight"].values
            )
    else:
        centroids["weight"] = oa_weight
        overall_coverage = total_coverage(oa_coverage, centroids["weight"].values)

    oa_coverage = [
        {"oa11cd": oa, "coverage": cov}
        for oa, cov in zip(centroids.index.values, oa_coverage)
    ]
    return {"total_coverage": overall_coverage, "oa_coverage": oa_coverage}
