from flask import Blueprint, request, make_response
from celery.result import AsyncResult
from celery import group, chord

import redis
import json
import msgpack
import os

from api.celery_tasks import (aggregate_yearly_results,
                              dropq_task_async,
                              dropq_task_small_async,
                              elasticity_gdp_task_async,
                              btax_async)

bp = Blueprint('endpoints', __name__)

queue_name = "celery"
client = redis.StrictRedis.from_url(os.environ.get("CELERY_BROKER_URL",
                                                   "redis://redis:6379/0"))


def dropq_endpoint(dropq_task):
    print('dropq endpoint')
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    print('inputs', inputs)
    result = dropq_task.apply_async(kwargs=inputs['inputs'],
                                    serializer='msgpack')
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength': length}
    return json.dumps(data)


def aggr_endpoint(task, callback):
    print('aggregating endpoint')
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    print('inputs', inputs)
    result = (chord(task.signature(kwargs=i,
                                   serializer='msgpack') for i in inputs)
              (callback.s()))
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength': length}
    return json.dumps(data)


@bp.route("/dropq_start_job", methods=['POST'])
def dropq_endpoint_full():
    return aggr_endpoint(dropq_task_async, aggregate_yearly_results)


@bp.route("/dropq_small_start_job", methods=['POST'])
def dropq_endpoint_small():
    return dropq_endpoint(dropq_task_small_async)


@bp.route("/btax_start_job", methods=['POST'])
def btax_endpoint():
    return dropq_endpoint(btax_async)


@bp.route("/elastic_gdp_start_job", methods=['POST'])
def elastic_endpoint():
    return dropq_endpoint(elasticity_gdp_task_async)


@bp.route("/dropq_get_result", methods=['GET'])
def dropq_results():
    job_id = request.args.get('job_id', '')
    async_result = AsyncResult(job_id)
    if async_result.ready() and async_result.successful():
        return async_result.result
    elif async_result.failed():
        print('traceback', async_result.traceback)
        return async_result.traceback
    else:
        resp = make_response('not ready', 202)
        return resp


@bp.route("/dropq_query_result", methods=['GET'])
def query_results():
    job_id = request.args.get('job_id', '')
    async_result = AsyncResult(job_id)
    print('async_result', async_result.state)
    if async_result.ready() and async_result.successful():
        return 'YES'
    elif async_result.failed():
        return 'FAIL'
    else:
        return 'NO'
