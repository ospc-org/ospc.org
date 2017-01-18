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
from ..constants import START_YEAR

AWS_KEY_ID = os.environ['AWS_KEY_ID']
AWS_SECRET_ID = os.environ['AWS_SECRET_ID']
NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
DUMP_DEBUG = os.environ.get('DUMP_DEBUG', None) == 'True'

if not os.path.exists("puf.csv.gz"):
    print "downloading records"
    aws_connection = S3Connection(AWS_KEY_ID, AWS_SECRET_ID)
    bucket = aws_connection.get_bucket('pufbucket')
    key = bucket.get_key("puf.csv.gz")
    key.get_contents_to_filename("puf.csv.gz")
    print "done downloading records"

app = Celery('tasks', broker=os.environ['REDISGREEN_URL'], backend=os.environ['REDISGREEN_URL'])

@app.task
def get_tax_results_async(mods, inputs_pk):
    print "mods is ", mods
    user_mods = package_up_vars(mods)
    print "user_mods is ", user_mods
    print "begin work"
    cur_path = os.path.abspath(os.path.dirname(__file__))
    tax_dta = pd.read_csv("puf.csv.gz", compression='gzip')
    mY_dec, mX_dec, df_dec, mY_bin, mX_bin, df_bin, fiscal_tots = dropq.run_models(tax_dta,
        num_years=NUM_BUDGET_YEARS, user_mods={START_YEAR:user_mods})

    if DUMP_DEBUG:
        with open("mY_dec.txt", "w") as f1:
            f1.write(json.dumps(mY_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')
    
        with open("mX_dec.txt", "w") as f1:
            f1.write(json.dumps(mX_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

        with open("df_dec.txt", "w") as f1:
            f1.write(json.dumps(df_dec, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

        with open("mY_bin.txt", "w") as f1:
            f1.write(json.dumps(mY_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

        with open("mX_bin.txt", "w") as f1:
            f1.write(json.dumps(mX_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

        with open("df_bin.txt", "w") as f1:
            f1.write(json.dumps(df_bin, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

        with open("fiscal_tots.txt", "w") as f1:
            f1.write(json.dumps(fiscal_tots, sort_keys=True, indent=4, separators=(',', ': ')) + '\n')

    results = {'mY_dec': mY_dec, 'mX_dec': mX_dec, 'df_dec': df_dec,
               'mY_bin': mY_bin, 'mX_bin': mX_bin, 'df_bin': df_bin,
               'fiscal_tots': fiscal_tots, 'inputs_pk': inputs_pk}

    print "end work"
    return results
