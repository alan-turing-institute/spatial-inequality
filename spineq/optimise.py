"""Main optimisation functions.
"""
from .data_fetcher import get_oa_centroids, get_oa_stats
from .utils import coverage_matrix, make_job_dict
from .weights import calc_location_weights

import numpy as np
import pandas as pd

import rq
from flask_socketio import SocketIO

import os
import datetime
import json


def optimise(
    n_sensors=20,
    theta=500,
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    traffic_weight=0,
    rq_job=False,
    socket=False,
    redis_url="redis://",
    save_result=False,
    save_plots=False,
    save_dir="",
    run_name="",
    **kwargs
):
    """Greedily place sensors to maximise coverage.
    
    Keyword Arguments:
        n_sensors {int} -- number of sensors to place (default: {20})
        theta {float} -- coverage decay rate (default: {500})
        
        population_weight, workplace_weight, pop_age_groups, traffic_weight --
            As defined in calc_location_weights (parameters directly passed to that
            function.)
        
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

    print("Fetching data...")
    if job:
        job.meta["status"] = "Fetching data"
        job.save_meta()

    if save_plots:
        from .plotting import plot_optimisation_result

        if save_dir:
            os.makedirs(save_dir, exist_ok=True)
        if not run_name:
            now = datetime.datetime.now()
            run_name = now.strftime("%Y%m%d%H%M")

    data = get_optimisation_inputs(
        population_weight=population_weight,
        workplace_weight=workplace_weight,
        pop_age_groups=pop_age_groups,
        combine=True,
    )
    oa_x = data["oa_x"]
    oa_y = data["oa_y"]
    oa_weight = data["oa_weight"]
    oa11cd = data["oa11cd"]

    n_poi = len(oa_x)

    # Compute coverage matrix: coverage at each OA due to a sensor placed at
    #  any other OA.
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    # binary array - 1 if sensor at this location, 0 if not
    sensors = np.zeros(n_poi)

    # coverage obtained with each number of sensors
    placement_history = []
    coverage_history = []
    oa_coverage = []

    for s in range(n_sensors):
        # greedily add sensors
        print("Placing sensor", s + 1, "out of", n_sensors, "... ", end="")

        if job:
            job.meta["status"] = "Placing sensor {} out of {}".format(s + 1, n_sensors)
            progress = 100 * s / n_sensors
            job.meta["progress"] = progress
            job.save_meta()
            if socket:
                socketIO.emit("jobProgress", {"job_id": job.id, "progress": progress})

        # initialise arrays to store best result so far
        best_total_coverage = 0
        best_sensors = sensors.copy()
        best_oa_coverage = sensors.copy()

        for site in range(n_poi):
            # try adding sensor at potential sensor site

            if sensors[site] == 1:
                # already have a sensor here, so skip to next
                continue

            else:
                new_sensors = sensors.copy()
                new_sensors[site] = 1

                # only keep coverages due to sites where a sensor is present
                mask_cov = np.multiply(coverage, new_sensors[np.newaxis, :])

                # coverage at each site = coverage due to nearest sensor
                max_mask_cov = np.max(mask_cov, axis=1)

                # Avg coverage = weighted sum across all points of interest
                new_coverage = (oa_weight * max_mask_cov).sum() / oa_weight.sum()

                if new_coverage > best_total_coverage:
                    # this site is the best site for next sensor found so far
                    best_new_site = oa11cd[site]
                    best_sensors = new_sensors.copy()
                    best_total_coverage = new_coverage
                    best_oa_coverage = max_mask_cov

        sensors = best_sensors.copy()
        placement_history.append(best_new_site)
        coverage_history.append(best_total_coverage)
        oa_coverage = best_oa_coverage.copy()

        print("coverage = {:.2f}".format(best_total_coverage))

        if save_plots == "all":
            result = make_result_dict(
                n_sensors,
                theta,
                oa_x,
                oa_y,
                oa11cd,
                sensors,
                best_total_coverage,
                oa_coverage,
                placement_history,
                coverage_history,
                pop_age_groups=pop_age_groups,
                population_weight=population_weight,
                workplace_weight=workplace_weight,
            )

            save_path = "{}/{}_nsensors_{:03d}.png".format(save_dir, run_name, s + 1)
            plot_optimisation_result(result, save_path=save_path, **kwargs)

    result = make_result_dict(
        n_sensors,
        theta,
        oa_x,
        oa_y,
        oa11cd,
        sensors,
        best_total_coverage,
        oa_coverage,
        placement_history,
        coverage_history,
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

    if save_plots == "final":
        save_path = "{}/{}_nsensors_{:03d}.png".format(save_dir, run_name, n_sensors)
        plot_optimisation_result(result, save_path=save_path, **kwargs)

    if save_result:
        result_file = "{}/{}_result.json".format(save_dir, run_name)
        with open(result_file, "w") as f:
            json.dump(result, f, indent=4)

    return result


def get_optimisation_inputs(
    population_weight=1,
    workplace_weight=0,
    pop_age_groups={
        "pop_total": {"min": 0, "max": 90, "weight": 1},
        "pop_children": {"min": 0, "max": 16, "weight": 0},
        "pop_elderly": {"min": 70, "max": 90, "weight": 0},
    },
    traffic_weight=0,
    combine=True,
):
    """Get input data in format needed for optimisation.
    
    Keyword Arguments:
        population_weight, workplace_weight, pop_age_groups, combine,
        traffic_weight --
            As defined in calc_location_weights (parameters directly passed to that
            function.)
    
    Returns:
        dict -- Optimisation input data
    """
    centroids = get_oa_centroids()
    weights = calc_location_weights(
        population_weight=population_weight,
        workplace_weight=workplace_weight,
        pop_age_groups=pop_age_groups,
        traffic_weight=traffic_weight,
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
        pop_age_groups {dict} -- population age groups (see calc_location_weights)
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

    result = {
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

    return result


def calc_coverage(sensors, oa_weight, theta=500):
    """Calculate the coverage of a network for arbitrary OA weightings.
    
    Arguments:
        sensors {list} -- List of sensors in the network, each sensors is a
        dict which must include the key "oa11cd".
        oa_weight {pd.Series} -- Weight for each OA, pandas series with index
        oa11cd and weights as values.
    
    Keyword Arguments:
        theta {int} -- coverage decay rate (default: {500})
    
    Returns:
        dict -- Coverage stats with keys "total_coverage" and "oa_coverage".
    """
    centroids = get_oa_centroids()
    centroids["weight"] = oa_weight

    centroids["has_sensor"] = 0
    for sensor in sensors:
        centroids.loc[sensor["oa11cd"], "has_sensor"] = 1

    oa11cd = centroids.index.values
    oa_x = centroids["x"].values
    oa_y = centroids["y"].values
    oa_weight = centroids["weight"].values
    sensors = centroids["has_sensor"].values

    n_poi = len(oa_x)

    coverage = coverage_matrix(oa_x, oa_y, theta=theta)

    # only keep coverages due to sites where a sensor is present
    mask_cov = np.multiply(coverage, sensors[np.newaxis, :])

    # coverage at each site = coverage due to nearest sensor
    oa_coverage = np.max(mask_cov, axis=1)

    # Avg coverage = weighted sum across all points of interest
    total_coverage = (oa_weight * oa_coverage).sum() / oa_weight.sum()

    oa_coverage = [
        {"oa11cd": oa11cd[i], "coverage": oa_coverage[i]} for i in range(n_poi)
    ]

    return {"total_coverage": total_coverage, "oa_coverage": oa_coverage}
