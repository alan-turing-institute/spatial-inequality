from .data_fetcher import get_data
from .utils import satisfaction_matrix

import numpy as np

import rq

def optimise(n_sensors=20, theta=500, rq_job=False):
    """Greedily place sensors to maximise satisfaction.
    
    Keyword Arguments:
        n_sensors {int} -- number of sensors to place (default: {20})
        theta {int} -- coverage decay rate (default: {500})
        rq_job {boolean} -- If True attempt to get the RQ job running this
        function and upate meta data with progress.

    Returns:
        dict -- optimisation result.
    """
    
    if rq_job:
        job = rq.get_current_job()
    else:
        job = None
    
    print("Fetching data...")
    if job:
        job.meta["status"] = "Fetching data"
        job.save_meta()
    
    data = get_data()
    poi_x = data["poi_x"]
    poi_y = data["poi_y"]
    poi_weight = data["poi_weight"]
    oa11cd = data["oa11cd"]
    
    n_poi = len(poi_x)
    satisfaction = satisfaction_matrix(poi_x, poi_y, theta=theta)
    
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
            job.meta["progress"] = 100 * s / n_sensors
            job.save_meta()
        
        best_total_satisfaction = 0
        best_sensors = sensors.copy()
        
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
                new_satisfaction = (poi_weight * max_mask_sat).sum() / poi_weight.sum()
                
                if new_satisfaction > best_total_satisfaction:
                    # this site is the best site for next sensor found so far
                    best_sensors = new_sensors.copy()
                    best_total_satisfaction = new_satisfaction
        
        sensors = best_sensors.copy()
        satisfaction_history.append(best_total_satisfaction)
        oa_satisfaction = max_mask_sat
        
        print("satisfaction = {:.2f}".format(best_total_satisfaction))
        
    sensor_locations = [{"x": poi_x[i], "y": poi_y[i],
                         "oa11cd": oa11cd[i]}
                        for i in range(n_poi) if sensors[i]==1]
    
    oa_satisfaction = [{"oa11cd": oa11cd[i],
                        "satisfaction": oa_satisfaction[i]}
                       for i in range(n_poi)]
    
    if job:
        job.meta["progress"] = 100
        job.meta["status"] = "Finished"
        job.save_meta()

    return {"sensors": sensor_locations,
            "total_satisfaction": best_total_satisfaction,
            "oa_satisfaction": oa_satisfaction}