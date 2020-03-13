from .data_fetcher import get_oa_centroids, get_oa_stats
from .utils import coverage_matrix, make_job_dict

import numpy as np
import pandas as pd

import rq
from flask_socketio import SocketIO

import os
import datetime
import json


def optimise(n_sensors=20, theta=500,
             age_weights=1, population_weight=1, workplace_weight=0,
             rq_job=False, socket=False, redis_url="redis://",
             save_result=False, save_plots=False, save_dir="", run_name="",
             **kwargs):
    """Greedily place sensors to maximise coverage.
    
    Keyword Arguments:
        n_sensors {int} -- number of sensors to place (default: {20})
        theta {int} -- coverage decay rate (default: {500})
        
        age_weights {float or pd.DataFrame} -- Either constant, in which case
        use same weighting for all ages, or a dataframe with index age (range
        between 0 and 90) and values weight (default: {1})
        population_weight {float} -- Weighting for residential population
        (default: {1})
        workplace_weight {float} -- Weighting for workplace population
        (default: {0})
        
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
    else:
        job = None
    if socket:
        socketIO = SocketIO(message_queue=redis_url)
       
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
    
    data = get_optimisation_inputs(age_weights=age_weights,
                                   population_weight=population_weight,
                                   workplace_weight=workplace_weight)
    oa_x = data["oa_x"]
    oa_y = data["oa_y"]
    oa_weight = data["oa_weight"]
    oa11cd = data["oa11cd"]
        
    n_poi = len(oa_x)
    coverage = coverage_matrix(oa_x, oa_y, theta=theta)
    
    # binary array - 1 if sensor at this location, 0 if not
    sensors = np.zeros(n_poi)

    # coverage obtained with each number of sensors
    coverage_history = []
    oa_coverage = []
    
    for s in range(n_sensors):
        # greedily add sensors
        print("Placing sensor", s+1, "out of", n_sensors, "... ", end='')
        
        if job:
            job.meta["status"] = "Placing sensor {} out of {}".format(s+1,
                                                                      n_sensors)
            progress = 100 * s / n_sensors
            job.meta["progress"] = progress
            job.save_meta()
            if socket:
                socketIO.emit("jobProgress", {"job_id": job.id,
                                              "progress": progress})

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
                    best_sensors = new_sensors.copy()
                    best_total_coverage = new_coverage
                    best_oa_coverage = max_mask_cov
        
        sensors = best_sensors.copy()
        coverage_history.append(best_total_coverage)
        oa_coverage = best_oa_coverage.copy()
        
        print("coverage = {:.2f}".format(best_total_coverage))
        
        if save_plots == "all":
            result = make_result_dict(n_sensors, theta, age_weights,
                                      population_weight, workplace_weight,
                                      oa_x, oa_y, oa11cd, sensors,
                                      best_total_coverage, oa_coverage)
            
            save_path = "{}/{}_nsensors_{:03d}.png".format(save_dir, run_name, s+1)
            plot_optimisation_result(result, save_path=save_path, **kwargs)
    
    result = make_result_dict(n_sensors, theta, age_weights, population_weight,
                              workplace_weight, oa_x, oa_y, oa11cd, sensors,
                              best_total_coverage, oa_coverage)
    
    if job:
        job.meta["progress"] = 100
        job.meta["status"] = "Finished"
        job.save_meta()
        if socket:
            jobDict = make_job_dict(job)
            jobDict["result"] = result
            socketIO.emit("jobFinished", jobDict)
            
    if save_plots == "final":
        save_path = "{}/{}_nsensors_{:03d}.png".format(save_dir, run_name,
                                                       n_sensors)
        plot_optimisation_result(result, save_path=save_path, **kwargs)
        
    if save_result:
        result_file = "{}/{}_result.json".format(save_dir, run_name)
        with open(result_file, "w") as f:
            json.dump(result, f, indent=4)

    return result


def calc_oa_weights(age_weights=1, population_weight=1, workplace_weight=0):
    """Calculate weighting factor for each OA.
    
    Keyword Arguments:
        age_weights {float or pd.DataFrame} -- Either constant, in which case
        use same weighting for all ages, or a dataframe with index age (range
        between 0 and 90) and values weight (default: {1})
        
        population_weight {float} -- Weighting for residential population
        (default: {1})
        
        workplace_weight {float} -- Weighting for workplace population
        (default: {0})
    
    Returns:
        pd.Series -- Weights for each OA (indexed by oa11cd).
    """
    
    data = get_oa_stats()
    population_ages = data["population_ages"]
    workplace = data["workplace"]
    
    if len(population_ages) != len(workplace):
        raise ValueError("Lengths of inputs don't match: population_ages={}, workplace={}"
                         .format(len(population_ages), len(workplace)))
    
    # weightings for residential population by age
    oa_pop_weight_age = population_ages * age_weights
    oa_pop_weight = oa_pop_weight_age.sum(axis=1)  # sum of weights for all ages
    if oa_pop_weight.sum() > 0:
        oa_pop_weight = oa_pop_weight / oa_pop_weight.sum()  # normalise so sum OA weights is 1
    
    # weightings for number of workers in OA (normalised to sum to 1)
    oa_work_weight = workplace / workplace.sum()
    
    # sum up weights and renormalise
    oa_all_weights = pd.DataFrame({"population": oa_pop_weight,
                                   "workplace": oa_work_weight})
    oa_all_weights["total"] = (workplace_weight*oa_all_weights["workplace"] +
                               population_weight*oa_all_weights["population"])
    oa_all_weights["total"] = (oa_all_weights["total"] /
                               oa_all_weights["total"].sum())
    
    return oa_all_weights["total"]


def get_optimisation_inputs(age_weights=1, population_weight=1,
                            workplace_weight=0):
    """Get input data in format needed for optimisation.
    
    Keyword Arguments:
        (all passed to cala_oa_weights)
        age_weights {float or pd.DataFrame} -- Either constant, in which case
        use same weighting for all ages, or a dataframe with index age (range
        between 0 and 90) and values weight (default: {1})
        
        population_weight {float} -- Weighting for residential population
        (default: {1})
        
        workplace_weight {float} -- Weighting for workplace population
        (default: {0})
    
    Returns:
        dict -- Optimisation input data
    """
    centroids = get_oa_centroids()
    weights = calc_oa_weights(age_weights=age_weights,
                              population_weight=population_weight,
                              workplace_weight=workplace_weight)
    
    if len(centroids) != len(weights):
        raise ValueError(
            "Lengths of inputs don't match: centroids={}, weights={}"
            .format(len(centroids), len(weights))
            )
    
    centroids["weight"] = weights
    
    oa11cd = centroids.index.values
    oa_x = centroids["x"].values
    oa_y = centroids["y"].values
    oa_weight = centroids["weight"].values
    
    return {"oa11cd": oa11cd, "oa_x": oa_x, "oa_y": oa_y,
            "oa_weight": oa_weight}


def make_result_dict(n_sensors, theta, age_weights, population_weight,
                     workplace_weight, oa_x, oa_y, oa11cd, sensors,
                     total_coverage, oa_coverage):
    n_poi = len(oa_x)
    sensor_locations = [{"x": oa_x[i], "y": oa_y[i],
                         "oa11cd": oa11cd[i]}
                        for i in range(n_poi) if sensors[i] == 1]
    
    oa_coverage = [{"oa11cd": oa11cd[i],
                    "coverage": oa_coverage[i]}
                    for i in range(n_poi)]
    
    if type(age_weights) == pd.Series:
        # can't directly pass pandas objects to json.dump
        age_weights = age_weights.to_dict()
    
    result = {"n_sensors": n_sensors,
              "theta": theta,
              "age_weights": age_weights,
              "population_weight": population_weight,
              "workplace_weight": workplace_weight,
              "sensors": sensor_locations,
              "total_coverage": total_coverage,
              "oa_coverage": oa_coverage}
    
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
        
    oa_coverage = [{"oa11cd": oa11cd[i],
                    "coverage": oa_coverage[i]}
                    for i in range(n_poi)]

    return {"total_coverage": total_coverage,
            "oa_coverage": oa_coverage}
