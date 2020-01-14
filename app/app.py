from flask import Flask, request

from redis import Redis
from rq import Queue
from rq.job import Job
from worker import conn, queue

from spineq.optimise import optimise

app = Flask(__name__)


@app.route("/")
def hello():
    return """To generate a network with 20 sensors go to <a href="/optimise?n_sensors=20">/optimise?n_sensors=20</a>"""


@app.route("/optimise", methods=["GET"])
def submit_optimise_job():
    if "n_sensors" in request.args:
        n_sensors = int(request.args.get("n_sensors"))
    else:
        n_sensors = 5
        
    if "theta" in request.args:
        theta = float(request.args.get("theta"))
    else:
        theta = 500
        
    job = queue.enqueue("spineq.optimise.optimise",
                        n_sensors=n_sensors,
                        theta=theta)
    
        
    return {"job_id": job.id}


@app.route("/job/<job_id>", methods=["GET"])
def get_job_result(job_id):
            
    job = Job.fetch(job_id, connection=conn)
    
    status = job.get_status()
    job.refresh()
    log = job.meta
    call_str = job.get_call_string()
    result = job.result
    print("LOG", log)        
    return {"job_id": job_id,
            "status": status,
            "log": log,
            "call_str": call_str,
            "result": result}


if __name__ == "__main__":
    app.run()