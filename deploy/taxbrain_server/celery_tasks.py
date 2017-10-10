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
celery_app = Celery('tasks2', broker=REDISGREEN_URL, backend=REDISGREEN_URL)
if MOCK_CELERY:
    CELERY_ALWAYS_EAGER = True
    BROKER_BACKEND = 'memory'
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
    def task(func):
        celery_app_like = Namespace(delay=func)
        return celery_app_like
    celery_app = Namespace(task=task)

#Create a Public Use File object
rn_seed = 80
if not MOCK_CELERY:
    tax_dta_full = pd.read_csv("puf.csv.gz", compression='gzip')
    tax_dta = tax_dta_full.sample(frac=0.02, random_state=rn_seed)
else:
    tax_dta_full = tax_dta = pd.DataFrame({})


def convert_int_key(user_mods):
    for key in user_mods:
        if hasattr(key, 'isdigit') and key.isdigit():
            user_mods[int(key)] = user_mods.pop(key)
    return user_mods


def dropq_task(year, user_mods, first_budget_year, beh_params, tax_data):
    print("user mods: ", user_mods)
    # The reform style indicates what kind of reform we ran.
    # A list of size 1 with 'True' indicates a standard TaxBrain run
    # A list of size > 1 indicates a file-based reform was run, where each
    # index indicates whether the reform dictionary was non-empty
    # The four reform dictionaries from file-based reforms are:
    # policy, behavior, growth, consumption (in that order)
    first_budget_year = int(first_budget_year)
    user_mods = convert_int_key(user_mods)
    print('first_year', first_budget_year)
    for reform_year in user_mods.keys():
        if user_mods.get(reform_year):
            for key in set(user_mods[reform_year]):
                if key.startswith('_BE_'):
                    user_mods[reform_year].pop(key)
        user_reform = {"policy": user_mods}
    print('user_reform', user_reform, user_mods)
    if beh_params:
        for x, y in beh_params.items():
            for z in y.keys():
                if z.isdigit():
                    convert_int_key(y)
        user_reform.update(beh_params)
    for key in EXPECTED_KEYS:
        if key not in user_reform:
            user_reform[key] = {}
    kw = dict(year_n=year, start_year=first_budget_year,
              taxrec_df=tax_data, user_mods=user_reform)
    print('keywords to dropq', {k: v for k, v in kw.items()
                                if k not in ('taxrec_df',)})
    (mY_dec_i, mX_dec_i, df_dec_i, pdf_dec_i, cdf_dec_i, mY_bin_i, mX_bin_i,
     df_bin_i, pdf_bin_i, cdf_bin_i, fiscal_tot_i,
     fiscal_tot_i_bl, fiscal_tot_i_ref) = taxcalc.dropq.run_nth_year_tax_calc_model(**kw)

    results = {'mY_dec': mY_dec_i, 'mX_dec': mX_dec_i, 'df_dec': df_dec_i,
               'pdf_dec': pdf_dec_i, 'cdf_dec': cdf_dec_i, 'mY_bin': mY_bin_i,
               'mX_bin': mX_bin_i, 'df_bin': df_bin_i, 'pdf_bin': pdf_bin_i,
               'cdf_bin': cdf_bin_i, 'fiscal_tot_diffs': fiscal_tot_i,
               'fiscal_tot_base': fiscal_tot_i_bl,
               'fiscal_tot_ref': fiscal_tot_i_ref}


    #Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version']
    results['dropq_version'] = vinfo['version']

    json_res = json.dumps(results)
    return json_res


@celery_app.task
def dropq_task_async(year, user_mods, first_budget_year, beh_params):
    print('dropq_task_async', year, user_mods, first_budget_year, beh_params)
    return dropq_task(year, user_mods, first_budget_year, beh_params, tax_dta_full)


@celery_app.task
def dropq_task_small_async(year, user_mods, first_budget_year, beh_params):
    return dropq_task(year, user_mods, first_budget_year, beh_params, tax_dta)


@celery_app.task
def elasticity_gdp_task_async(year, user_mods, first_budget_year, elast_params):

    if first_budget_year:
        first_year = int(first_budget_year)
    else:
        first_year = int(user_mods.keys()[0])
    user_mods = convert_int_key(user_mods)
    user_reform = {'policy': user_mods, 'gdp_elasticity': {'value': elast_params}}
    # combine elast_params with user_mods
    for key in EXPECTED_KEYS:
        if key not in user_reform:
            user_reform[key] = {}
    # combine elast_params with user_mods
    print("ELASTICITY user mods: ", user_reform)

    gdp_elast_i = taxcalc.dropq.run_nth_year_gdp_elast_model(year_n=year,
                                                             start_year=first_year,
                                                             taxrec_df=tax_dta,
                                                             user_mods=user_reform)

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
def btax_async(user_mods):
    print("user mods: ", user_mods)
    results = {}
    tables = runner_json_tables(**user_mods)
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
    return json.dumps(results)


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
