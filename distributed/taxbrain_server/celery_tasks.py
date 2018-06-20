
from argparse import Namespace
import json
import os
import sys
import tempfile
import time

from celery import Celery, states
from celery.exceptions import Ignore, Terminated
import pandas as pd

import btax
from btax.front_end_util import runner_json_tables
import taxcalc
import ogusa
from taxbrain_server import run_ogusa


EXPECTED_KEYS = ('policy', 'consumption', 'behavior',
                'growdiff_baseline', 'growdiff_response',
                'gdp_elasticity',)
TEST_FAIL = False

from taxbrain_server.utils import set_env
globals().update(set_env())
accept_content = ['msgpack', 'json']
celery_app = Celery('tasks2', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.update(
    task_serializer='json',
    accept_content=['msgpack', 'json'],
)

def convert_int_key(user_mods):
    for key in user_mods:
        if hasattr(key, 'isdigit') and key.isdigit():
            user_mods[int(key)] = user_mods.pop(key)
    return user_mods


def dropq_task(year_n, user_mods, first_budget_year, use_puf_not_cps=True, use_full_sample=True):
    print(
        'keywords to dropq',
        dict(
            year_n=year_n,
            start_year=int(first_budget_year),
            use_puf_not_cps=use_puf_not_cps,
            use_full_sample=use_full_sample,
            user_mods=user_mods
        )
    )

    results = taxcalc.tbi.run_nth_year_taxcalc_model(
        year_n=year_n,
        start_year=int(first_budget_year),
        use_puf_not_cps=use_puf_not_cps,
        use_full_sample=use_full_sample,
        user_mods=user_mods
    )

    #Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    results['dropq_version'] = vinfo['version']

    json_res = json.dumps(results)
    return json_res


@celery_app.task(name='taxbrain_server.celery_tasks.dropq_task_async')
def dropq_task_async(year, user_mods, first_budget_year, use_puf_not_cps=True):
    print('dropq_task_async', year, user_mods, first_budget_year, use_puf_not_cps)
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=True)


@celery_app.task(name='taxbrain_server.celery_tasks.dropq_task_small_async')
def dropq_task_small_async(year, user_mods, first_budget_year, use_puf_not_cps=True):
    print('dropq_task_small_async', year, user_mods, first_budget_year, use_puf_not_cps)
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=False)


@celery_app.task(name='taxbrain_server.celery_tasks.elasticity_gdp_task_async')
def elasticity_gdp_task_async(year_n, user_mods, first_budget_year,
                              gdp_elasticity, use_puf_not_cps=True):
    print("kw to dropq", dict(
        year_n=year_n,
        start_year=int(first_budget_year),
        use_puf_not_cps=use_puf_not_cps,
        use_full_sample=True,
        user_mods=user_mods,
        gdp_elasticity=gdp_elasticity
    ))

    gdp_elast_i = taxcalc.tbi.run_nth_year_gdp_elast_model(
        year_n=year_n,
        start_year=int(first_budget_year),
        use_puf_not_cps=use_puf_not_cps,
        use_full_sample=True,
        user_mods=user_mods,
        gdp_elasticity=gdp_elasticity
    )

    results = {'elasticity_gdp': gdp_elast_i}
    #Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    results['dropq_version'] = vinfo['version']

    json_res = json.dumps(results)
    return json_res


@celery_app.task(name='taxbrain_server.celery_tasks.ogusa_async')
def ogusa_async(user_mods, ogusa_params, guid):
    print("user mods: ", user_mods)
    user_mods = convert_int_key(user_mods)
    user_reform = {'policy': user_mods}
    for key in EXPECTED_KEYS:
        if key not in user_reform:
            user_reform[key] = {}
    diff_data = run_ogusa.run_micro_macro(reform=user_reform,
                                          user_params=ogusa_params,
                                          guid=guid)

    diff_table = taxcalc.dropq.format_macro_results(diff_data)
    results = {'df_ogusa': diff_table}
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    results['dropq_version'] = vinfo['version']

    #ogusa uses different version convention
    ogvinfo = ogusa._version.get_versions()
    ogusa_version = ogvinfo['version']
    results['ogusa_version'] = ogusa_version
    json_res = json.dumps(results)
    return json_res


@celery_app.task(name='taxbrain_server.celery_tasks.btax_async')
def btax_async(user_mods, start_year):
    print("user mods: ", user_mods)
    user_mods['start_year'] = start_year
    print("submitting btax data: ", user_mods)
    results = {}
    tables = json.loads(runner_json_tables(**user_mods))
    if tables.get("json_table"):
        results.update(tables["json_table"])
        if tables.get("dataframes"):
            dataframes = json.loads(tables["dataframes"])
            for x, y in list(dataframes.items()):
                dataframes[x] = json.loads(y)
            results["dataframes"] = dataframes
    else:
        results.update(tables)
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    results['dropq_version'] = vinfo['version']
    binfo = btax._version.get_versions()
    results['btax_version'] = binfo['version']
    json_res = json.dumps(results)
    return json_res
