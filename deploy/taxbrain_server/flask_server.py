from __future__ import print_function, unicode_literals, division
import argparse
from contextlib import contextmanager
import copy
import datetime
from functools import partial
import json
import os
import uuid
import threading
from threading import Thread, Event, Lock
import time

from flask import Flask, request, make_response
import pandas as pd
import taxcalc
from pandas.util.testing import assert_frame_equal
import requests
import redis
from retrying import retry

from taxbrain_server.utils import set_env
globals().update(set_env())
from taxbrain_server.celery_tasks import (celery_app, dropq_task_async,
                                          dropq_task_small_async,
                                          ogusa_async, elasticity_gdp_task_async,
                                          btax_async, example_async, MOCK_CELERY)



app = Flask('sampleapp')

server_url = "http://localhost:5050"

queue_name = "celery"
if not MOCK_CELERY:
    client = redis.Redis(host="localhost", port=6379)
else:
    client = None
RUNNING_JOBS = {}
TRACKING_TICKETS = {}
SLEEP_INTERVAL_TICKET_CHECK = 30
TRACKING_TICKETS_PATH = os.path.join(os.path.dirname(__file__),
                                     '.TRACKING_TICKETS')
if MOCK_CELERY:
    TRACKING_TICKETS_PATH += '-TESTING'
TICKET_CHECK_COUNTER = 0
TICKET_WRITE_MOD = int(os.environ.get('TICKET_WRITE_MOD', '1'))
EXIT_EVENT = None
TICKET_LOCK = None
IN_PRODUCTION = True
TIMEOUT_IN_SECONDS = 800.0


@contextmanager
def ticket_lock_context():
    global TICKET_LOCK
    TICKET_LOCK.acquire()
    try:
        yield
    finally:
        TICKET_LOCK.release()

def dropq_endpoint(dropq_task):
    if request.method == 'POST':
        year_n = request.form['year']
        user_mods = json.loads(request.form['user_mods'])
        beh_params = None if 'behavior_params' not in request.form else json.loads(request.form['behavior_params'])
        first_budget_year = None if 'first_budget_year' not in request.form else request.form['first_budget_year']
    else:
        year_n = request.args.get('year', '')
        first_budget_year = None
        beh_params = None

    year_n = int(year_n)
    print("beh params", beh_params, " user_mods: ", user_mods)
    raw_results = dropq_task.delay(year_n, user_mods, first_budget_year, beh_params)
    RUNNING_JOBS[raw_results.id] = raw_results
    length = client.llen(queue_name) + 1
    results = {'job_id':str(raw_results), 'qlength':length}
    return str(json.dumps(results))


@app.route("/dropq_start_job", methods=['GET', 'POST'])
def dropq_endpoint_full():
    return dropq_endpoint(dropq_task_async)


@app.route("/dropq_small_start_job", methods=['GET', 'POST'])
def dropq_endpoint_small():
    return dropq_endpoint(dropq_task_small_async)


@app.route("/btax_start_job", methods=['POST'])
def btax_endpoint():
    year = request.form['year']
    # TODO: this assumes a single year is the key at highest
    # level.
    user_mods = tuple(json.loads(request.form['user_mods']).values())[0]
    print('user_mods', user_mods)
    year = int(year)
    raw_results = btax_async.delay(user_mods)
    RUNNING_JOBS[raw_results.id] = raw_results
    length = client.llen(queue_name) + 1
    results = {'job_id':str(raw_results), 'qlength':length}
    return str(json.dumps(results))


@app.route("/elastic_gdp_start_job", methods=['POST'])
def elastic_endpoint():

    # TODO: this assumes a single year is the key at highest
    # level.
    user_mods = tuple(json.loads(request.form['user_mods']).values())[0]
    year_n = int(request.form['year'])
    print('user_mods', user_mods, 'year_n', year_n)
    user_mods = json.loads(request.form['user_mods'])
    elast_params = None if 'elasticity_params' not in request.form else json.loads(request.form['elasticity_params'])
    first_budget_year = None if 'first_budget_year' not in request.form else request.form['first_budget_year']
    user_mods = {int(k): v for k, v in user_mods.iteritems()}
    elast_params = elast_params or user_mods.values()[0].pop('elastic_gdp', elast_params)
    if not isinstance(elast_params, (float, int)):
        elast_params = float(elast_params[0])
    print("elast params", elast_params, " user_mods: ", user_mods)
    raw_results = elasticity_gdp_task_async.delay(year_n, user_mods, first_budget_year, elast_params)
    RUNNING_JOBS[raw_results.id] = raw_results
    length = client.llen(queue_name) + 1
    results = {'job_id': str(raw_results), 'qlength': length}
    return str(json.dumps(results))


@app.route("/dropq_get_result", methods=['GET'])
def dropq_results():
    job_id = request.args.get('job_id', '')
    results = RUNNING_JOBS[job_id]
    if results.ready() and results.successful():
        tax_result = results.result
        return tax_result
    elif results.failed():
        return results.traceback
    else:
        resp = make_response('not ready', 202)
        return resp


@app.route("/dropq_query_result", methods=['GET'])
def query_results():
    job_id = request.args.get('job_id', '')
    if job_id in RUNNING_JOBS:
        results = RUNNING_JOBS[job_id]
        if results.ready() and results.successful():
            return "YES"
        elif results.failed():
            return "FAIL"
        else:
            return "NO"
    else:
        return "FAIL"


@app.route('/example_start_job', methods=['POST'])
def example():

    if request.method == 'POST':
        year = request.form.get('first_year', 2015)
        user_mods = json.loads(request.form['user_mods'])
        user_mods = {int(k): v for k, v in user_mods.iteritems()}
    else:
        year = request.args.get('year', '')

    with ticket_lock_context():
        job = example_async.delay()
        RUNNING_JOBS[job.id] = job
        print('job_id', job)

    return json.dumps({'job_id': str(job)})



@app.route('/ogusa_start_job', methods=['POST'])
def ogusa_start_job():
    user_mods = json.loads(request.form['user_mods'])
    ogusa_params = json.loads(request.form['ogusa_params'])

    user_mods = {int(k): v for k, v in user_mods.iteritems()}

    with ticket_lock_context():
        guid = uuid.uuid1().hex
        job = ogusa_async.delay(user_mods=user_mods, ogusa_params=ogusa_params, guid=guid)
        RUNNING_JOBS[job.id] = job
        print('job_id', job)
        print('GUID IS ', guid)

    return json.dumps({'job_id': str(job),
                       'guid': guid})


def sleep_function(seconds):
    def sleep_function_dec(func):
        def new_func(*args, **kwargs):
            global EXIT_EVENT
            try:
                while not EXIT_EVENT.isSet():
                    func(*args, **kwargs)
                    for repeat in range(int(seconds)):
                        if EXIT_EVENT.isSet():
                            return
                        time.sleep(1)
            except KeyboardInterrupt:
                EXIT_EVENT.set()
                print('KeyboardInterrupt')
                return
        return new_func
    return sleep_function_dec


class BadResponse(ValueError):
    pass


def retry_exception_or_not(exception):
    if isinstance(exception, BadResponse):
        return False
    return True


@retry(wait_fixed=7000, stop_max_attempt_number=4,
       retry_on_exception=retry_exception_or_not)
def do_callback(job_id, callback, params):
    """wait wait_fixed milliseconds between each separate attempt to
    do callback this without exception.  Retry it up to stop_max_attempt_number
    retries, unless the exception is a BadResponse, which is a specific
    error dictionary from returned by callback response that is successfully
    json.loaded."""
    callback_response = None
    print("callback is ", callback)
    try:
        callback_response = requests.get(callback, params=params, timeout=TIMEOUT_IN_SECONDS)
        if not callback_response.status_code == 200:
            # DO not retry if an error message is returned
            print('ERROR (no retry) in callback_response: {0}'.format(callback_response))
            raise BadResponse(str(callback_response))
        return True
    except Exception as e:
        if callback_response is not None:
            content = callback_response._content
            first_message = "Failed to json.loads callback_response"
        else:
            first_message = "No content. Probable timeout."
            content = ""
        msg = first_message +\
            " with exception {0}".format(repr(e)) +\
            " for ticket id {0}:{1}".format(job_id, content) +\
            ".  May retry."
        print(msg)
        raise


def job_id_check():
    global TRACKING_TICKETS
    global TICKET_CHECK_COUNTER
    print('starting a job id check')
    with ticket_lock_context():
        old_tracking_tickets = copy.deepcopy(TRACKING_TICKETS)
        TICKET_CHECK_COUNTER += 1
        to_pop = []
        print("TRACKING_TICKETS is ", TRACKING_TICKETS, threading.current_thread())
        for job_id in list(TRACKING_TICKETS.keys()):
            print("job id is ", job_id)
            if job_id not in RUNNING_JOBS:
                print("UNKNOWN JOB IN TRACKING TICKETS: ", job_id)
                print("REMOVING JOB")
                del TRACKING_TICKETS[job_id]
            else:
                task = RUNNING_JOBS[job_id]
                if task.failed() or task.ready():
                    to_pop.append((task, job_id))
        for task, job_id in to_pop:
            ticket_dict = TRACKING_TICKETS.pop(job_id)
            callback = ticket_dict['callback']
            # TODO decide on exception handling here
            # raise exception if 1 ticket's callback fails? or just log it?
            params = dict(ticket_dict['params'])
            params['job_id'] = ticket_dict['job_id']
            #params['status'] = ticket_dict[result]
            params['status'] = task.status
            if IN_PRODUCTION:
                resp = do_callback(job_id, callback, params)
            else:
                print("Calling back with params: ", params)

        if TICKET_CHECK_COUNTER >= TICKET_WRITE_MOD:
            # periodically dump the TRACKING_TICKETS to json
            # if changed
            if old_tracking_tickets != TRACKING_TICKETS:
                TICKET_CHECK_COUNTER = 0
                with open(TRACKING_TICKETS_PATH, 'w') as f:
                    f.write(json.dumps(TRACKING_TICKETS))


@app.route("/register_job", methods=['POST'])
def register_job():
    global TRACKING_TICKETS
    callback = request.form.get('callback', False)
    job_id = request.form.get('job_id', False)
    print("job_id in register_job is ", job_id)
    params = json.loads(request.form.get('params', "{}"))
    if not callback or not job_id:
        return make_response(json.dumps({'error': "Expected arguments of " +
                                                  "job_id, callback, and " +
                                                  "optionally params."}), 400)
    msg = "Start checking: job_id {0} with params {1} and callback {2}"
    print(msg.format(job_id, params, callback))
    now = datetime.datetime.utcnow().isoformat()
    with ticket_lock_context():
        TRACKING_TICKETS[job_id] = {'params': params,
                                    'started': now,
                                    'callback': callback,
                                    'job_id': job_id,
                                    }
        return json.dumps({'registered': TRACKING_TICKETS[job_id], })


@app.route('/pop_job_id', methods=['POST'])
def pop():
    global TRACKING_TICKETS
    with ticket_lock_context():

        job_id = request.args.get('job_id', '')
        if job_id in TRACKING_TICKETS:
            resp = json.dumps({'popped': TRACKING_TICKETS.pop(job_id)})
        else:
            resp =  make_response(json.dumps({'job_id': job_id,
                              'error': 'job_id not present'}), 400)
        return resp


@app.route('/current_tickets_tracker', methods=['GET'])
def current_tickets_tracker():
    with ticket_lock_context():
        return json.dumps(TRACKING_TICKETS)


@app.route('/example_success_callback', methods=['POST'])
def example_success_callback():
    return json.dumps({'ok': 'example_success_callback'})


def cli():
    parser = argparse.ArgumentParser(description="Run flask server")
    parser.add_argument('-s', '--sleep-interval',
                        help="How long to sleep between status checks",
                        default=SLEEP_INTERVAL_TICKET_CHECK,
                        type=float)
    parser.add_argument('-p', '--port', help="Port on which to run",
                        default=5050, required=False)
    parser.add_argument('-i', '--ignore-cached-tickets',
                        help="Skip the loading of tracking tickets from " +
                             "{0}.  Testing only.".format(TRACKING_TICKETS_PATH))
    return parser.parse_args()


@contextmanager
def app_tracking_context(args=None):
    global TRACKING_TICKETS
    global EXIT_EVENT
    global TICKET_LOCK
    EXIT_EVENT = Event()
    TICKET_LOCK = Lock()
    if not args:
        args = cli()
    if os.path.exists(TRACKING_TICKETS_PATH) and not args.ignore_cached_tickets:
        # load any tickets if they exist
        with open(TRACKING_TICKETS_PATH, 'r') as f:
            TRACKING_TICKETS = json.load(f)

    @sleep_function(args.sleep_interval)
    def checking_tickets_at_interval():
        return job_id_check()
    try:
        checker_thread = Thread(target=checking_tickets_at_interval)
        checker_thread.daemon = True
        checker_thread.start()
        if not MOCK_CELERY:
            print('Run forever')
            yield app.run(host='0.0.0.0', port=args.port, debug=True, use_reloader=False)
        else:
            print('Mock app')
            yield app
    except Exception as e:
        EXIT_EVENT.set()
        time.sleep(3)
        raise
    finally:
        # dump all the standing tickets no matter what
        with ticket_lock_context():
            with open(TRACKING_TICKETS_PATH, 'w') as f:
                f.write(json.dumps(TRACKING_TICKETS))

def main(args=None):

    with app_tracking_context(args=args) as app:
        return 0


if __name__ == "__main__":
    main()
