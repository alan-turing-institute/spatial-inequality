"""Starts a RQ worker, which will extract jobs from the Redis
server and processes them.
"""

import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_QUEUE
from rq import Connection, Queue, Worker

redis_url = f"redis://{REDIS_HOST}:{REDIS_PORT}"
conn = redis.from_url(redis_url)

queue = Queue(REDIS_QUEUE, connection=conn)
listen = [REDIS_QUEUE]

if __name__ == "__main__":
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
