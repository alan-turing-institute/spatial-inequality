"""
Demonstration of how to interact with the API via WebSockets
"""

from socketIO_client import SocketIO, LoggingNamespace

JOB_ID = None


def print_message(message):
    print('MESSAGE', message)


def print_job(job):
    print("JOB", job)

    
def print_queue(queue):
    print("QUEUE", queue)


def job_finished(job_id):
    global JOB_ID
    JOB_ID = job_id
    print("JOB FINISHED", job_id)


# Define host and callbacks
socketIO = SocketIO('localhost', 5000, LoggingNamespace)
socketIO.on('message', print_message)
socketIO.on('job', print_job)
socketIO.on('queue', print_queue)
socketIO.on('jobFinished', job_finished)

# Make connection
print("CONNECT")
socketIO.emit('connect')
socketIO.wait(seconds=1)
print("----------")

# Submit an optimisation job: client emits submitJob, server responds by
# emitting job
print("SUBMIT JOB")
socketIO.emit('submitJob', {"n_sensors": 3, "theta": 789})
socketIO.wait(seconds=1)
print("----------")

print("WAITING")
socketIO.wait(seconds=20)
# should see a jobFinished message once the job has completed
print("----------")


# Get job result/status: client emits "getJob", server responds by emitting
# "job" event
print("GET JOB")
socketIO.emit('getJob', JOB_ID)
socketIO.wait(seconds=1)
print("----------")

# List jobs on the queue and their status: client emits "getQueue", server
# responds by emitting "queue" event
print("LIST QUEUE")
socketIO.emit('getQueue')
socketIO.wait(seconds=1)
print("----------")

# Delete a job: client emits "deleteJob", server responds by emitting "message"
# event
print("DELETE JOB")
socketIO.emit('deleteJob', JOB_ID)
socketIO.wait(seconds=2)
print("----------")


# Delete everything in the queue: client emits "deleteQueue", server responds
# by emitting "message" event
print("DELETE QUEUE")
socketIO.emit('deleteQueue')
socketIO.wait(seconds=2)
print("----------")
