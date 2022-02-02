"""Creates the Flask and Flask-Socketio endpoints for the
optimisation backend.
"""
import rq
from config import FLASK_HOST, FLASK_PORT, REDIS_HOST, REDIS_PORT
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from rq.job import Job
from worker import conn, queue

from spineq.utils import make_age_range, make_job_dict

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
    """Run an optimisation job.

    Query parameters:
        - n_sensors: generate a network with this many sensors (default: 5)
        - theta: decay rate for coverage measure (default: 500)
        - min_age: minimum age to consider (default: 0)
        - max_age: maximum age to consider (default: 90)
        - population_weight: overall weight for residential population coverage (default: 1)
        - workplace_weight: overall weight for place of work coverage (default: 0)

    Returns:
        dict -- json of information about the created job, including its
        id in the queue.
    """

    if "n_sensors" in request.args:
        n_sensors = int(request.args.get("n_sensors"))
    else:
        n_sensors = 5

    if "theta" in request.args:
        theta = float(request.args.get("theta"))
    else:
        theta = 500

    if "min_age" in request.args:
        min_age = float(request.args.get("min_age"))
    else:
        min_age = 0

    if "max_age" in request.args:
        max_age = float(request.args.get("max_age"))
    else:
        max_age = 90

    age_weights = make_age_range(min_age=min_age, max_age=max_age)

    if "population_weight" in request.args:
        population_weight = float(request.args.get("population_weight"))
    else:
        population_weight = 1

    if "workplace_weight" in request.args:
        workplace_weight = float(request.args.get("workplace_weight"))
    else:
        workplace_weight = 0

    job_dict = submit_optimise_job(
        n_sensors=n_sensors,
        theta=theta,
        age_weights=age_weights,
        population_weight=population_weight,
        workplace_weight=workplace_weight,
        socket=False,
        redis_url=redis_url,
    )

    return job_dict


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


@socketio.on("connect")
def test_connect():
    """Open sockdtio connection"""
    emit("message", {"data": "Connected"})


@socketio.on("disconnect")
def test_disconnect():
    print("Client disconnected")


@socketio.on("submitJob")
def socket_optimise_job(parameters):
    """Run an optimisation job.

    Arguments:
         parameters {dict} -- Optimisation parameters including:
             - n_sensors: generate a network with this many sensors.
             - theta: decay rate for coverage measure.
             - min_age: minimum age to consider (default: 0)
             - max_age: maximum age to consider (default: 90)
             - population_weight: overall weight for residential population coverage (default: 1)
             - workplace_weight: overall weight for place of work coverage (default: 0)

     Returns:
         dict -- json of information about the created job, including its
         id in the queue.
    """

    if "n_sensors" not in parameters.keys() or "theta" not in parameters.keys():
        emit("job", {"code": 400, "message": "Must supply n_sensors and theta."})

    else:
        if "min_age" in parameters.keys():
            min_age = parameters["min_age"]
        else:
            min_age = 0

        if "max_age" in parameters.keys():
            max_age = parameters["max_age"]
        else:
            max_age = 90

        age_weights = make_age_range(min_age=min_age, max_age=max_age)

        if "population_weight" in parameters.keys():
            population_weight = parameters["population_weight"]
        else:
            population_weight = 1

        if "workplace_weight" in parameters.keys():
            workplace_weight = parameters["workplace_weight"]
        else:
            workplace_weight = 0

        job_dict = submit_optimise_job(
            n_sensors=parameters["n_sensors"],
            theta=parameters["theta"],
            age_weights=age_weights,
            population_weight=population_weight,
            workplace_weight=workplace_weight,
            socket=True,
            redis_url=redis_url,
        )
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


def submit_optimise_job(
    n_sensors=5,
    theta=500,
    age_weights=1,
    population_weight=1,
    workplace_weight=0,
    socket=False,
    redis_url="redis://",
):
    """Submit an optimisation job to the Redis queue.

    Keyword Arguments:
        - n_sensors {int}: generate a network with this many sensors (default: {5})
        - theta {float}: decay rate for coverage measure (default: {500})
        - min_age {int}: minimum age to consider (default: {0})
        - max_age {int}: maximum age to consider (default: {90})
        - population_weight {float}: overall weight for residential population coverage (default: {1})
        - workplace_weight {float}: overall weight for place of work coverage (default: {0})

    Returns:
        dict -- information about the created job, including its
        id in the queue, as created by utils.make_job_dict.
    """

    job = queue.enqueue(
        "spineq.optimise.optimise",
        meta={"status": "Queued", "progress": 0},
        ttl=86400,  # maximum time to stay in queue (seconds)
        job_timeout=3600,  # max job execution time (seconds)
        result_ttl=86400,  # how long to keep result (seconds)
        n_sensors=n_sensors,
        theta=theta,
        rq_job=True,
        socket=socket,
        redis_url=redis_url,
        age_weights=age_weights,
        population_weight=population_weight,
        workplace_weight=workplace_weight,
    )

    return make_job_dict(job)


def get_job(job_id):
    """Get information about a job on the Redis queue.

    Arguments:
        job_id {str} -- id of job to get from the queue

    Returns:
        dict -- information about the created job, including its
        id in the queue, as created by utils.make_job_dict."""
    try:
        job = Job.fetch(job_id, connection=conn)
        return make_job_dict(job)

    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404, "message": "No job with id " + job_id}}


def get_queue():
    """List job ids available to query in the queue.

    Returns:
        dict -- json with list of ids under key job_ids.
    """
    queued = queue.job_ids
    started = queue.started_job_registry.get_job_ids()
    finished = queue.finished_job_registry.get_job_ids()
    failed = queue.failed_job_registry.get_job_ids()

    jobs = {
        "queued": queued,
        "started": started,
        "finished": finished,
        "failed": failed,
    }

    return jobs


def clear_queue():
    """Remove all jobs from the queue.

    Returns:
        dict -- json with result of whether queue was successfully emptied.
    """
    n_removed = queue.empty()
    n_remaining = len(queue.job_ids)

    if n_remaining == 0:
        return {
            "code": 200,
            "message": "Removed all jobs from the queue",
            "n_jobs_removed": n_removed,
            "n_jobs_remaining": n_remaining,
        }

    else:
        return {
            "code": 400,
            "message": "Failed to remove some jobs from the queue.",
            "n_jobs_removed": n_removed,
            "n_jobs_remaining": n_remaining,
        }


def delete_job(job_id):
    """Delete a single job from the queue.

    Arguments:
        job_id {str} -- id of job to get from the queue

    Returns:
        dict -- json with result of whether job was successfully deleted.
    """

    try:
        job = Job.fetch(job_id, connection=conn)

    except rq.exceptions.NoSuchJobError:
        return {"error": {"code": 404, "message": "No job with id " + job_id}}

    # delete and verify can't get the job from the queue anymore
    try:
        job.delete()
        job = Job.fetch(job_id, connection=conn)
        return {"error": {"code": 400, "message": "Delete failed for job " + job_id}}
    except rq.exceptions.NoSuchJobError:
        return {"code": 200, "message": "Successfully deleted job " + job_id}


if __name__ == "__main__":
    app.run(host=FLASK_HOST, port=FLASK_PORT)
