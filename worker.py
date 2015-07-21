from rq import Worker, Queue, Connection
import os
import redis
import taxcalc
from taxcalc import Parameters, Records, Calculator
import boto
import pandas as pd
from boto.s3.connection import S3Connection


listen = ['high', 'default', 'low']

redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')

conn = redis.from_url(redis_url)

if __name__ == '__main__':

    AWS_KEY_ID = 'AKIAJOWWEOJHG3P6WNWQ'
    AWS_SECRET_ID = 'sg1aVcP0XKGosg7dsqGDlJY7IHbmSsgFQxGDb80N'
    aws_connection = S3Connection(AWS_KEY_ID, AWS_SECRET_ID)
    bucket = aws_connection.get_bucket('pufbucket')
    key = bucket.get_key("puf_small")
    key.get_contents_to_filename(os.path.join("webapp", "apps", "taxbrain", "puf2.csv"))
    from custom_work import *
    with Connection(conn):
        worker = GeventWorker(map(Queue, listen))
        worker.work()
