import os
import redis
from rq import Worker, Queue, Connection
from alerting import redis_connection

listen = ['default']

with Connection(redis_connection):
    worker = Worker(map(Queue, listen))
    worker.work()