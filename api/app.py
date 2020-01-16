from flask import Flask, request, jsonify, send_from_directory

from redis import Redis
import rq
from rq.job import Job
from worker import conn, queue

from spineq.optimise import optimise

from config import FLASK_HOST, FLASK_PORT

app = Flask(__name__)


@app.route("/")
def home():
    return """spineq-api:<br>
                Submit optimisation job: /optimise?n_sensors=&lt;n_sensors&gt;<br>
                Get job status and results: /job/&lt;job_id&gt;<br>
                View jobs available on the queue: /queue<br>
                Delete all jobs from the queue: /queue/deleteall<br>
                Remove one job from the queue: /queue/delete/&lt;job_id&gt;
    """


@app.route("/optimise")
def submit_optimise_job():
    """Run an optimisation job. Query parameters:
        - n_sensors: generate a network with this many sensors. 
        - theta: decay rate for satisfaction measure.
    
    Returns:
        dict -- json of information about the created job, including its
        id in the queue.
        
        
    @api {get} /optimise:id Request User information
    @apiName GetUser
    @apiGroup User

    @apiParam {Number} id Users unique ID.

    @apiSuccess {String} firstname Firstname of the User.
    @apiSuccess {String} lastname  Lastname of the User.
    """
    
    if "n_sensors" in request.args:
        n_sensors = int(request.args.get("n_sensors"))
    else:
        n_sensors = 5
        
    if "theta" in request.args:
        theta = float(request.args.get("theta"))
    else:
        theta = 500
        
    job = queue.enqueue("spineq.optimise.optimise",
                        meta={"status": "Queued", "progress": 0},
                        ttl=86400,  # maximum time to stay in queue (seconds)
                        job_timeout=3600,  # max job execution time (seconds)
                        result_ttl=86400,  # how long to keep result (seconds)
                        n_sensors=n_sensors,
                        theta=theta,
                        rq_job=True)  
            
    return make_job_dict(job)


@app.route("/job/<job_id>", methods=["GET"])
def get_job(job_id):
    """Get a job from the queue using its id.
    
    Arguments:
        job_id {str} -- id for the job on the queue to query.
    
    Returns:
        dict -- json containing job status information and its result if the
        job has finished.
    """
    
    try:
        job = Job.fetch(job_id, connection=conn)
        return make_job_dict(job)
        
    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404,
                          "message": "No job with id "+job_id}}, 404
    


@app.route("/queue", methods=["GET"])
def get_job_ids():
    """List job ids available to query in the queue.
    
    Returns:
        dict -- json with list of ids under key job_ids. 
    """
    queued = queue.job_ids
    started = queue.started_job_registry.get_job_ids()
    finished = queue.finished_job_registry.get_job_ids()
    failed = queue.failed_job_registry.get_job_ids()
    
    jobs = {"queued": queued,
            "started": started,
            "finished": finished,
            "failed": failed}
    
    return jsonify(jobs)


@app.route("/queue/deleteall")
def clear_queue():
    """Remove all jobs from the queue.
    
    Returns:
        dict -- json with result of whether queue was successfully emptied.
    """
    n_removed = queue.empty()
    n_remaining = len(queue.job_ids)
    
    if n_remaining == 0:      
        return {"code": 200,
                "message": "Removed all jobs from the queue",
                "n_jobs_removed": n_removed,
                "n_jobs_remaining": n_remaining}
     
    else:
        return {"code": 400,
                "message": "Failed to remove some jobs from the queue.",
                "n_jobs_removed": n_removed,
                "n_jobs_remaining": n_remaining}


@app.route("/queue/delete/<job_id>")
def delete_job(job_id):
    """Delete a single job from the queue.
    
    Returns:
        dict -- json with result of whether job was successfully deleted.
    """
    
    try:
        job = Job.fetch(job_id, connection=conn)
        
    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404,
                          "message": "No job with id "+job_id}}, 404
        
    # delete and verify can't get the job from the queue anymore
    try:
        job.delete()
        job = Job.fetch(job_id, connection=conn)
        return {"error": {"code": 400,
                    "message": "Delete failed for job "+job_id}}, 400
    except rq.exceptions.NoSuchJobError:
        return {"code": 200,
                "message": "Successfully deleted job "+job_id}, 200


def make_job_dict(job):
    status = job.get_status()
    call_str = job.get_call_string()
    result = job.result
    
    if "progress" in job.meta.keys():
        progress = job.meta["progress"]
    else:
        progress = 0
    
    if "status" in job.meta.keys():
        last_message = job.meta["status"]
    
    return {"job_id": job.id,
            "call_str": call_str,
            "status": status,
            "progress": progress,
            "last_message": last_message,       
            "result": result}


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
