#celery_status_server.py

from flask import Flask, request, make_response
from celery import Celery
from celery.app.control import Inspect
from celery.result import AsyncResult
import datetime
import requests
import os
import json
import time
import sys
import subprocess as sp
from functools import partial
import example_async
"""
nohup redis-server &
nohup celery -A example_async worker -P eventlet -l info &
"""
server_app = Flask('celery_status_server')
port = 5070
server_url = "http://localhost:{0}".format(port)

TICKET_IDS_WATCHED = {}
m = '--module'
if not m in sys.argv:
    mod = 'example_async'
    print('NOTE: defaulting to example_async celery_app because --module not given.')
else:
    mod = sys.argv[sys.argv.index(m) + 1]
celery_app = __import__(mod).__dict__['celery_app']

def inspect_celery():
    global TICKET_IDS_WATCHED
    return_val = {}
    missing = []
    i = celery_app.control.inspect()
    print('i',i)
    for label, worker_check in zip(('active', 'scheduled'),(i.active(), i.scheduled())):
        print('worker_check', worker_check)
        if worker_check:
            for worker_id, worker_dict_list in worker_check.items():

                for worker_dict in worker_dict_list:
                    print('worker_dict', worker_dict)
                    request = worker_dict.get('request', {})
                    job_id = worker_dict.get('id', request.get('id', None))
                    eta = worker_dict.get('eta', None)
                    if job_id in TICKET_IDS_WATCHED:
                        print('in TICKET_IDS_WATCHED')
                        return_val[worker_dict['id']] = {'inputs': TICKET_IDS_WATCHED[job_id].copy(),
                                                         'status': label,
                                                         'eta': eta,
                                                         }
                    else:
                        print('ticket_id', job_id, 'is not in TICKET_IDS_WATCHED', worker_dict)
    for key in TICKET_IDS_WATCHED:
        if key not in return_val:
            return_val[key] = {'inputs': TICKET_IDS_WATCHED[key].copy(),
                               'status': 'done'}
            if celery_app.AsyncResult(key).ready():
                missing.append(key)
    response = {}
    for key in missing:
        worker_dict = TICKET_IDS_WATCHED[key]
        if 'callback' in worker_dict:
            worker_dict['id'] = key
            callback = worker_dict['callback']
            if not callback.startswith('http://'):
                callback = 'http://' + callback
            worker_dict['callback'] = callback
            response = requests.post(callback, data=worker_dict)
            try:
                response = response.json()
            except Exception as e:
                print(response._content)
                print('failed to .json() the above')
                response = str(response._content)
        if key in return_val:
            return_val[key] = {'callback_response': response}
        else:
            return_val[key]['callback_response'] = response
    return return_val

@server_app.route('/example_async', methods=['POST'])
def example():

    ticket_id =  example_async.example_async.delay()
    print('ticket_id', ticket_id)
    url = '{0}/register_job?email={1}&ticket_id={2}&callback=google.com'.format(server_url, ticket_id, ticket_id)
    return json.dumps({'ticket_id': str(ticket_id)})

@server_app.route("/register_job", methods=['POST'])
def register_job():
    print('hit register_job')
    global TICKET_IDS_WATCHED
    if not request.args.get('email', False) and not request.args.get('ticket_id', False):
        return make_response(json.dumps({'error': "Expected keys of email and ticket_id"}), 400)
    ticket_id = request.args['ticket_id']
    email = request.args['email']
    print("Start checking: {} with email {}".format(ticket_id, email))

    TICKET_IDS_WATCHED[ticket_id] = {'email': email,
                                     'started': datetime.datetime.utcnow().isoformat(),
                                     'callback': request.args.get('callback','')}
    return json.dumps(inspect_celery())

@server_app.route("/celery_status_server", methods=['GET'])
def celery_status_server():
    print("results here")
    ticket_id = request.args.get('ticket_id','')
    if ticket_id:
        return json.dumps({ticket_id: inspect_celery().get('ticket_id')})
    return json.dumps(inspect_celery())

@server_app.route('/pop_ticket_id', methods=['POST'])
def pop():
    global TICKET_IDS_WATCHED
    ticket_id = request.args.get('ticket_id','')
    if ticket_id in TICKET_IDS_WATCHED:
        return json.dumps(TICKET_IDS_WATCHED.pop(ticket_id))
    return make_response({'ticket_id': ticket_id,'error': 'not-present'}, 400)

if __name__ == "__main__":
    server_app.debug = True
    server_app.run(host='localhost', port=port)
