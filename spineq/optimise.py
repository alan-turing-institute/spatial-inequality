from .data_fetcher import get_oa_centroids, get_oa_stats
from .utils import satisfaction_matrix, make_job_dict

import numpy as np
import pandas as pd

import rq
from flask_socketio import SocketIO


def optimise(n_sensors=20, theta=500,
             age_weights=1, population_weight=1, workplace_weight=0,
             rq_job=False, socket=False, redis_url="redis://"):
    """Greedily place sensors to maximise satisfaction.
    
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
    
    data = get_optimisation_inputs(age_weights=age_weights,
                                   population_weight=population_weight,
                                   workplace_weight=workplace_weight)
    oa_x = data["oa_x"]
    oa_y = data["oa_y"]
    oa_weight = data["oa_weight"]
    oa11cd = data["oa11cd"]
        
    n_poi = len(oa_x)
    satisfaction = satisfaction_matrix(oa_x, oa_y, theta=theta)
    
    # binary array - 1 if sensor at this location, 0 if not
    sensors = np.zeros(n_poi)

    # satisfaction obtained with each number of sensors
    satisfaction_history = []
    oa_satisfaction = []
    
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
        best_total_satisfaction = 0
        best_sensors = sensors.copy()
        best_oa_satisfaction = sensors.copy()
        
        for site in range(n_poi):
            # try adding sensor at potential sensor site
            
            if sensors[site] == 1:
                # already have a sensor here, so skip to next
                continue
            
            else:
                new_sensors = sensors.copy()
                new_sensors[site] = 1
                
                # only keep satisfactions due to sites where a sensor is present
                mask_sat = np.multiply(satisfaction, new_sensors[np.newaxis, :])

                # satisfaction at each site = satisfaction due to nearest sensor
                max_mask_sat = np.max(mask_sat, axis=1)
                
                # Avg satisfaction = weighted sum across all points of interest
                new_satisfaction = (oa_weight * max_mask_sat).sum() / oa_weight.sum()
                
                if new_satisfaction > best_total_satisfaction:
                    # this site is the best site for next sensor found so far
                    best_sensors = new_sensors.copy()
                    best_total_satisfaction = new_satisfaction
                    best_oa_satisfaction = max_mask_sat
        
        sensors = best_sensors.copy()
        satisfaction_history.append(best_total_satisfaction)
        oa_satisfaction = best_oa_satisfaction.copy()
        
        print("satisfaction = {:.2f}".format(best_total_satisfaction))
        
    sensor_locations = [{"x": oa_x[i], "y": oa_y[i],
                         "oa11cd": oa11cd[i]}
                        for i in range(n_poi) if sensors[i] == 1]
    
    oa_satisfaction = [{"oa11cd": oa11cd[i],
                        "satisfaction": oa_satisfaction[i]}
                       for i in range(n_poi)]
    
    result = {"sensors": sensor_locations,
              "total_satisfaction": best_total_satisfaction,
              "oa_satisfaction": oa_satisfaction}
    
    if job:
        job.meta["progress"] = 100
        job.meta["status"] = "Finished"
        job.save_meta()
        if socket:
            jobDict = make_job_dict(job)
            jobDict["result"] = result
            socketIO.emit("jobFinished", jobDict)

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
        dict -- Optimisation input data
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
