from socketIO_client import SocketIO, LoggingNamespace

def print_message(message):
    print('MESSAGE', message)


def print_job(job):
    print("JOB", job)
    
def print_queue(queue):
    print("QUEUE", queue)


socketIO = SocketIO('localhost', 5000, LoggingNamespace)
socketIO.on('message', print_message)
socketIO.on('job', print_job)
socketIO.on("queue", print_queue)


print("CONNECT")
socketIO.emit('connect')
socketIO.wait(seconds=1)
print("----------")

print("SUBMIT JOB")
socketIO.emit('submitJob', {"n_sensors": 13, "theta": 789})
socketIO.wait(seconds=1)
print("----------")

print("GET JOB")
socketIO.emit('getJob', "<THE JOB ID>")
socketIO.wait(seconds=1)
print("----------")

print("LIST QUEUE")
socketIO.emit('getQueue')
socketIO.wait(seconds=1)
print("----------")

print("DELETE JOB")
socketIO.emit('deleteJob', "<THE JOB ID>")
socketIO.wait(seconds=1)
print("----------")

print("DELETE QUEUE")
socketIO.emit('deleteQueue')
socketIO.wait(seconds=1)
print("----------")
