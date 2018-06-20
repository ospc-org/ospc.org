from __future__ import print_function, unicode_literals, division, absolute_import

from flask import Blueprint, request, make_response
from celery.result import AsyncResult

import redis
import json
import msgpack

from taxbrain_server.utils import set_env
globals().update(set_env())
from .celery_tasks import (celery_app, dropq_task_async,
                          dropq_task_small_async,
                          ogusa_async, elasticity_gdp_task_async,
                          btax_async)

print('name', dropq_task_async.name)
bp = Blueprint('api', __name__)

queue_name = "celery"
client = redis.StrictRedis(host="redis", port=6379)

def dropq_endpoint(dropq_task):
    # year_n = request.form['year']
    # user_mods = json.loads(request.form['user_mods'])
    # first_budget_year = request.form['first_budget_year']
    # use_puf_not_cps = request.form['use_puf_not_cps']
    #
    # year_n = int(year_n)
    # # use_puf_not_cps passed as string. If for some reason it is not supplied
    # # we default to True i.e. using the PUF file
    # if use_puf_not_cps in ('True', 'true') or use_puf_not_cps is None:
    #     use_puf_not_cps = True
    # else:
    #     use_puf_not_cps = False
    print('dropq endpoint')
    # print('data',
    # data = request.get_data()
    # print('data data', data)
    data = request.get_data()
    inputs = msgpack.loads(data, encoding='utf8',
                           use_list=True)
    print('inputs', inputs)
    result = dropq_task.delay(**inputs['inputs'])
    length = client.llen(queue_name) + 1
    data = {'job_id': str(result), 'qlength':length}
    return json.dumps(data)


@bp.route("/dropq_start_job", methods=['POST'])
def dropq_endpoint_full():
    return dropq_endpoint(dropq_task_async)


@bp.route("/dropq_small_start_job", methods=['POST'])
def dropq_endpoint_small():
    print('dropq_task_small_async name', dropq_task_small_async.name)
    return dropq_endpoint(dropq_task_small_async)


@bp.route("/btax_start_job", methods=['POST'])
def btax_endpoint():
    # TODO: this assumes a single year is the key at highest
    # level.
    user_mods = tuple(json.loads(request.form['user_mods']).values())[0]
    print('user_mods', user_mods)
    start_year = int(request.form['first_budget_year'])
    raw_results = btax_async.delay(user_mods, start_year)
    length = client.llen(queue_name) + 1
    results = {'job_id': str(raw_results), 'qlength':length}
    json_res = json.dumps(results)
    return json_res

@bp.route("/elastic_gdp_start_job", methods=['POST'])
def elastic_endpoint():
    user_mods = json.loads(request.form['user_mods'])
    year_n = int(request.form['year'])
    print('user_mods', user_mods, 'year_n', year_n)
    elast_params = json.loads(request.form['gdp_elasticity'])
    first_budget_year = request.form['first_budget_year']
    print("elast params", elast_params, " user_mods: ", user_mods)
    use_puf_not_cps = request.form['use_puf_not_cps']
    # use_puf_not_cps passed as string. If for some reason it is not supplied
    # we default to True i.e. using the PUF file
    if use_puf_not_cps in ('True', 'true') or use_puf_not_cps is None:
        use_puf_not_cps = True
    else:
        use_puf_not_cps = False
    raw_results = elasticity_gdp_task_async.delay(
        year_n,
        user_mods,
        first_budget_year,
        elast_params,
        use_puf_not_cps=use_puf_not_cps
    )
    length = client.llen(queue_name) + 1
    results = {'job_id': str(raw_results), 'qlength': length}
    return str(json.dumps(results))

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
