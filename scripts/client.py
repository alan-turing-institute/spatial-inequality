"""
Demonstration of how to interact with the API via WebSockets
"""

import time
import socketio

JOB_ID = None

# Define host and callbacks
sio = socketio.Client()


@sio.on("message")
def print_message(message):
    print("MESSAGE", message)


@sio.on("job")
def print_job(job):
    print("JOB", job)


@sio.on("queue")
def print_queue(queue):
    print("QUEUE", queue)


@sio.on("jobFinished")
def job_finished(data):
    global JOB_ID
    JOB_ID = data["job_id"]
    print("JOB FINISHED", data)


@sio.on("jobProgress")
def print_progress(progress):
    print("PROGRESS", progress)


# Make connection
print("CONNECT")
# sio.connect("https://optimisation-backend.azurewebsites.net")
sio.connect("http://localhost:5000")

time.sleep(1)
print("----------")

# Submit an optimisation job: client emits submitJob, server responds by
# emitting job
print("SUBMIT JOB")
sio.emit(
    "submitJob",
    {
        "n_sensors": 3,
        "theta": 789,
        "min_age": 3,
        "max_age": 18,
        "population_weight": 0.5,
        "workplace_weight": 0.5,
    },
)
time.sleep(1)
print("----------")

print("WAITING 1 MINUTE FOR JOB PROGRESS")
time.sleep(60)
# should see a jobFinished message once the job has completed
print("----------")

# Get job result/status: client emits "getJob", server responds by emitting
# "job" event
print("GET JOB")
sio.emit("getJob", JOB_ID)
time.sleep(1)
print("----------")

# List jobs on the queue and their status: client emits "getQueue", server
# responds by emitting "queue" event
print("LIST QUEUE")
sio.emit("getQueue")
time.sleep(1)
print("----------")

# Delete a job: client emits "deleteJob", server responds by emitting "message"
# event
print("DELETE JOB")
sio.emit("deleteJob", JOB_ID)
time.sleep(1)
print("----------")

print("DISCONNECT")
sio.disconnect()
