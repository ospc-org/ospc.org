import taxcalc
import dropq
import pandas as pd
import os
import json


from rq import Queue
from worker import conn
import time
q = Queue(connection=conn)

def test_func(personal_exemp, exemp_start, phase_out):
    job = q.enqueue(do_work, personal_exemp, exemp_start, phase_out)
    time.sleep(1)
    while(not job.result):
        time.sleep(1)
    return job.result

def do_work(personal_exemp, exemp_start, phase_out):
    global tax_dta
    myvars = {}
    myvars['_rt4'] = [0.39]
    user_mods = json.dumps(myvars)
    print "begin work"
    cur_path = os.path.abspath(os.path.dirname(__file__))
    tax_dta = pd.read_csv(os.path.join(cur_path, "./puf2.csv"))
    mY_dec, df_dec, mY_bin, df_bin = dropq.run_models(tax_dta, user_mods=user_mods)
    print "end work"

    results = (personal_exemp - exemp_start) * phase_out
    return results
