import taxcalc
import pandas as pd
import os
import json
from taxcalc import *
import dropq

from celery import Celery
import time

import boto
from boto.s3.connection import S3Connection
import os

from .helpers import *

app = Celery('tasks', broker=os.environ['REDISGREEN_URL'], backend=os.environ['REDISGREEN_URL'])

@app.task
def get_tax_results_async(mods, inputs_pk):
    raise NotImplementedError('This function needs to be filled out in btax as it is in taxbrain')