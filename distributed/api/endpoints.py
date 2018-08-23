from flask import Blueprint, request, make_response
from celery.result import AsyncResult
from celery import chord

import redis
import json
import msgpack
import os

from api.celery_tasks import (taxbrain_postprocess,
                              taxbrain_elast_postprocess,
                              dropq_task_async,
                              dropq_task_small_async,
                              taxbrain_elast_async,
                              btax_async, file_upload_test)

bp = Blueprint('endpoints', __name__)

queue_name = "celery"
client = redis.StrictRedis.from_url(os.environ.get("CELERY_BROKER_URL",
                                                   "redis://redis:6379/0"))


def aggr_endpoint(compute_task, postprocess_task):
    print('aggregating endpoint')
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    print('inputs', inputs)
    result = (chord(compute_task.signature(kwargs=i, serializer='msgpack')
              for i in inputs))(postprocess_task.signature(
                serializer='msgpack'))
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength': length}
    return json.dumps(data)


def endpoint(task):
    print('dropq endpoint')
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    print('inputs', inputs)
    result = task.apply_async(kwargs=inputs[0],
                              serializer='msgpack')
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength': length}
    return json.dumps(data)


def file_test_endpoint(task):
    print('file test endpoint')
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    result = task.apply_async(kwargs=inputs[0], serializer='msgpack')
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength': length}
    return json.dumps(data)


@bp.route("/dropq_start_job", methods=['POST'])
def dropq_endpoint_full():
    return aggr_endpoint(dropq_task_async, taxbrain_postprocess)


@bp.route("/dropq_small_start_job", methods=['POST'])
def dropq_endpoint_small():
    return aggr_endpoint(dropq_task_small_async, taxbrain_postprocess)


@bp.route("/btax_start_job", methods=['POST'])
def btax_endpoint():
    return endpoint(btax_async)


@bp.route("/elastic_gdp_start_job", methods=['POST'])
def elastic_endpoint():
    return aggr_endpoint(taxbrain_elast_async, taxbrain_elast_postprocess)


@bp.route("/file_upload_test", methods=['POST'])
def file_upload_test_endpoint():
    return file_test_endpoint(file_upload_test)


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
