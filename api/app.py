from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from flask_socketio import SocketIO, emit

from redis import Redis
import rq
from rq.job import Job
from worker import conn, queue

from spineq.optimise import optimise
from spineq.utils import make_job_dict

from config import FLASK_HOST, FLASK_PORT, REDIS_HOST, REDIS_PORT

redis_url = "redis://{}:{}".format(REDIS_HOST, REDIS_PORT)


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", message_queue=redis_url)

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
def route_optimise_job():
    """Run an optimisation job. Query parameters:
        - n_sensors: generate a network with this many sensors. 
        - theta: decay rate for coverage measure.
    
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
        
    return submit_optimise_job(n_sensors=n_sensors, theta=theta)


@app.route("/job/<job_id>", methods=["GET"])
def route_get_job(job_id):
    """Get a job from the queue using its id.
    
    Arguments:
        job_id {str} -- id for the job on the queue to query.
    
    Returns:
        dict -- json containing job status information and its result if the
        job has finished.
    """
    return get_job(job_id)
    

@app.route("/queue", methods=["GET"])
def route_get_queue():
    """List job ids available to query in the queue.
    
    Returns:
        dict -- json with list of ids under key job_ids. 
    """
    return get_queue()


@app.route("/queue/deleteall")
def route_clear_queue():
    """Remove all jobs from the queue.
    
    Returns:
        dict -- json with result of whether queue was successfully emptied.
    """
    return clear_queue()


@app.route("/queue/delete/<job_id>")
def route_delete_job(job_id):
    """Delete a single job from the queue.
    
    Returns:
        dict -- json with result of whether job was successfully deleted.
    """
    return delete_job(job_id)


@socketio.on('connect')
def test_connect():
    emit('message', {'data': 'Connected'})


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')


@socketio.on("submitJob")
def socket_optimise_job(parameters):
    """Run an optimisation job. Query parameters:
        - n_sensors: generate a network with this many sensors. 
        - theta: decay rate for coverage measure.
    
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
    
    if "n_sensors" not in parameters.keys() or "theta" not in parameters.keys():
        emit("job", {"code": 400,
                     "message": "Must supply n_sensors and theta."})
    
    else:
        job_dict = submit_optimise_job(n_sensors=parameters["n_sensors"],
                                       theta=parameters["theta"],
                                       socket=True,
                                       redis_url=redis_url)
        emit("job", job_dict)


@socketio.on("getJob")
def socket_get_job(job_id):
    """Get a job from the queue using its id.
    
    Arguments:
        job_id {str} -- id for the job on the queue to query.
    
    Returns:
        dict -- json containing job status information and its result if the
        job has finished.
    """
    
    job_dict = get_job(job_id)
    emit("job", job_dict)
    

@socketio.on("getQueue")
def socket_get_queue():
    """List job ids available to query in the queue.
    
    Returns:
        dict -- json with list of ids under key job_ids. 
    """
    emit("queue", get_queue())


@socketio.on("deleteQueue")
def socket_clear_queue():
    """Remove all jobs from the queue.
    
    Returns:
        dict -- json with result of whether queue was successfully emptied.
    """
    emit("message", clear_queue())


@socketio.on("deleteJob")
def socket_delete_job(job_id):
    """Delete a single job from the queue.
    
    Returns:
        dict -- json with result of whether job was successfully deleted.
    """
    emit("message", delete_job(job_id))


def submit_optimise_job(n_sensors=5, theta=500,
                        socket=False, redis_url="redis://"):
    """Run an optimisation job. Query parameters:
        - n_sensors: generate a network with this many sensors. 
        - theta: decay rate for coverage measure.
    
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
     
    job = queue.enqueue("spineq.optimise.optimise",
                        meta={"status": "Queued", "progress": 0},
                        ttl=86400,  # maximum time to stay in queue (seconds)
                        job_timeout=3600,  # max job execution time (seconds)
                        result_ttl=86400,  # how long to keep result (seconds)
                        n_sensors=n_sensors,
                        theta=theta,
                        rq_job=True,
                        socket=socket,
                        redis_url=redis_url)  
            
    return make_job_dict(job)


def get_job(job_id):
    try:
        job = Job.fetch(job_id, connection=conn)
        return make_job_dict(job)
        
    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404,
                          "message": "No job with id "+job_id}}
        

def get_queue():
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
    
    return jobs


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
        

def delete_job(job_id):
    """Delete a single job from the queue.
    
    Returns:
        dict -- json with result of whether job was successfully deleted.
    """
    
    try:
        job = Job.fetch(job_id, connection=conn)
        
    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404,
                          "message": "No job with id "+job_id}}
        
    # delete and verify can't get the job from the queue anymore
    try:
        job.delete()
        job = Job.fetch(job_id, connection=conn)
        return {"error": {"code": 400,
                    "message": "Delete failed for job "+job_id}}
    except rq.exceptions.NoSuchJobError:
        return {"code": 200,
                "message": "Successfully deleted job "+job_id}
        

if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
