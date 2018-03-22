from __future__ import print_function, unicode_literals, division
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
import btax.run_btax as run_btax
from btax.front_end_util import runner_json_tables
import taxcalc
import ogusa
import run_ogusa
from taxcalc import Policy, Calculator


EXPECTED_KEYS = ('policy', 'consumption', 'behavior',
                'growdiff_baseline', 'growdiff_response',
                'gdp_elasticity',)
TEST_FAIL = False

from utils import set_env
globals().update(set_env())
celery_app = Celery('tasks2', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
if MOCK_CELERY:
    CELERY_ALWAYS_EAGER = True
    BROKER_BACKEND = 'memory'
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    def task(func):
        celery_app_like = Namespace(delay=func)
        return celery_app_like
    celery_app = Namespace(task=task)

tax_dta_full = tax_dta = pd.DataFrame({})


def convert_int_key(user_mods):
    for key in user_mods:
        if hasattr(key, 'isdigit') and key.isdigit():
            user_mods[int(key)] = user_mods.pop(key)
    return user_mods


def dropq_task(year_n, user_mods, first_budget_year, use_puf_not_cps=True, use_full_sample=True):
    # convert all year values from string to int
    for k in user_mods:
        user_mods[k] = convert_int_key(user_mods[k])

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

    results = taxcalc.tbi.run_nth_year_tax_calc_model(
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


@celery_app.task
def dropq_task_async(year, user_mods, first_budget_year, use_puf_not_cps=True):
    print('dropq_task_async', year, user_mods, first_budget_year, use_puf_not_cps)
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=True)


@celery_app.task
def dropq_task_small_async(year, user_mods, first_budget_year, use_puf_not_cps=True):
    print('dropq_task_small_async', year, user_mods, first_budget_year, use_puf_not_cps)
    return dropq_task(year, user_mods, first_budget_year,
                      use_puf_not_cps=use_puf_not_cps, use_full_sample=False)


@celery_app.task
def elasticity_gdp_task_async(year_n, user_mods, first_budget_year,
                              gdp_elasticity, use_puf_not_cps=True):
    # convert all string year values to int
    # all dictionaries in user_mods are empty
    user_mods["policy"] = convert_int_key(user_mods["policy"])
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


@celery_app.task
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


@celery_app.task
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
            for x, y in dataframes.items():
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


@celery_app.task
def example_async():
    "example async 4 second function for testing"
    time.sleep(4)
    example_table = {'ok': 1}
    results = {'df_ogusa': example_table}

    if TEST_FAIL:
        raise Exception()

    #Add version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    dqvinfo = taxcalc.dropq._version.get_versions()
    results['dropq_version'] = vinfo['version']

    #ogusa uses different version convention
    ogvinfo = ogusa._version.get_versions()
    ogusa_version = ogvinfo['version']
    results['ogusa_version'] = ogusa_version
    json_res = json.dumps(results)
    return json_res


def main():
    import subprocess as sp
    pfx = sys.prefix
    args = [os.path.join(pfx, 'bin', 'celery'),
            '-A',
            'taxbrain_server.celery_tasks',
            'worker',
            '--concurrency=1',
            '-P',
            'eventlet',
            '-l',
            'info']
    proc = sp.Popen(args,
                    env=os.environ,
                    stdout=sp.PIPE,
                    stderr=sp.STDOUT)
    while proc.poll() is None:
        line = proc.stdout.readline().decode()
        print(line, end='')
    print(proc.stdout.read().decode())
    return proc.poll()


if __name__ == "__main__":
    main()
