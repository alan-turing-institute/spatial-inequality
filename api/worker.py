"""Starts a RQ worker, which will extract jobs from the Redis
server and processes them.
"""
import os
from config import REDIS_HOST, REDIS_PORT, REDIS_QUEUE

import redis
from rq import Worker, Queue, Connection


redis_url = "redis://{}:{}".format(REDIS_HOST, REDIS_PORT)
conn = redis.from_url(redis_url)

queue = Queue(REDIS_QUEUE, connection=conn)
listen = [REDIS_QUEUE]

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
