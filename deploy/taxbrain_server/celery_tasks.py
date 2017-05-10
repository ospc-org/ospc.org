from __future__ import print_function
from argparse import Namespace
import json
import os
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
import tempfile
import os

EXPECTED_KEYS = ('policy', 'consumption', 'behavior',
                'growdiff_baseline', 'growdiff_response',
                'gdp_elasticity',)
TEST_FAIL = False
MOCK_CELERY = bool(int(os.environ.get('MOCK_CELERY', 0)))
REDISGREEN_URL = os.environ.get('REDISGREEN_URL', "redis://localhost:6379")
if not REDISGREEN_URL and not MOCK_CELERY:
    raise ValueError('Expected environment variable for redis: REDISGREEN_URL')
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


def taxio_reform_formatter(user_mods):
    reform_mods = user_mods['reform']
    reform_tmp = tempfile.NamedTemporaryFile(delete=False)
    reform_tmp.write(reform_mods)
    reform_tmp.close()

    assump_mods = user_mods['assumptions']
    if assump_mods:
        assump_tmp = tempfile.NamedTemporaryFile(delete=False)
        assump_tmp.write(assump_mods)
        assump_tmp.close()
        assumptions = assump_tmp.name
    else:
        assumptions = None

    user_reform = Calculator.read_json_param_files(reform_tmp.name, assumptions)
    if not 'gdp_elasticity' in user_reform:
        user_reform['gdp_elasticity'] = {}
    os.remove(reform_tmp.name)
    if assump_mods:
        os.remove(assump_tmp.name)
    policy = user_reform.get('policy') or {}
    user_reform['policy'] = convert_int_key(policy)
    return user_reform


def dropq_task(year, user_mods, first_budget_year, beh_params, tax_data):
    print("user mods: ", user_mods)
    # The reform style indicates what kind of reform we ran.
    # A list of size 1 with 'True' indicates a standard TaxBrain run
    # A list of size > 1 indicates a file-based reform was run, where each
    # index indicates whether the reform dictionary was non-empty
    # The four reform dictionaries from file-based reforms are:
    # policy, behavior, growth, consumption (in that order)
    reform_style = [True]
    if first_budget_year is not None:
        first_year = int(first_budget_year)
    else:
        first_year = int(user_mods.keys()[0])

    user_mods = convert_int_key(user_mods)
    print('first_year', first_year)
    if user_mods.get(first_year):
        for key in set(user_mods[first_year]):
            if key.startswith('_BE_'):
                user_mods[first_year].pop(key)
        user_reform = {"policy": user_mods}
    else:
        user_reform = taxio_reform_formatter(user_mods)
    print('user_reform', user_reform, user_mods)
    reform_style = [True if x else False for x in user_reform]
    if beh_params:
        # combine behavioral parameters with user_mods
        beh_first_year = beh_params['first_year']
        del beh_params['first_year']
        beh_dict = {int(beh_first_year):beh_params}
        user_reform['behavior'] = beh_dict
    for key in EXPECTED_KEYS:
        if key not in user_reform:
            user_reform[key] = {}
    kw = dict(year_n=year, start_year=first_year,
              taxrec_df=tax_data, user_mods=user_reform)
    print('keywords to dropq', {k: v for k, v in kw.items()
                                if k not in ('taxrec_df',)})
    (mY_dec_i, mX_dec_i, df_dec_i, pdf_dec_i, cdf_dec_i, mY_bin_i, mX_bin_i,
     df_bin_i, pdf_bin_i, cdf_bin_i, fiscal_tot_i,
     fiscal_tot_i_bl, fiscal_tot_i_ref) = taxcalc.dropq.run_nth_year_model(**kw)

    results = {'mY_dec': mY_dec_i, 'mX_dec': mX_dec_i, 'df_dec': df_dec_i,
               'pdf_dec': pdf_dec_i, 'cdf_dec': cdf_dec_i, 'mY_bin': mY_bin_i,
               'mX_bin': mX_bin_i, 'df_bin': df_bin_i, 'pdf_bin': pdf_bin_i,
               'cdf_bin': cdf_bin_i, 'fiscal_tot_diffs': fiscal_tot_i,
               'fiscal_tot_base': fiscal_tot_i_bl,
               'fiscal_tot_ref': fiscal_tot_i_ref,
               'reform_style': reform_style}


    #Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    results['dropq_version'] = vinfo['version'] + '.' + vinfo['full'][:6]

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
    results['taxcalc_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    results['dropq_version'] = vinfo['version'] + '.' + vinfo['full'][:6]

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
    results['taxcalc_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    results['dropq_version'] = vinfo['version'] + '.' + vinfo['full'][:6]

    #ogusa uses different version convention
    ogvinfo = ogusa._version.get_versions()
    ogusa_version = ".".join([ogvinfo['version'], ogvinfo['full-revisionid'][:6]])
    results['ogusa_version'] = ogusa_version
    json_res = json.dumps(results)
    return json_res


@celery_app.task
def btax_async(user_mods):
    print("user mods: ", user_mods)
    results = {}
    results.update(runner_json_tables(**user_mods))
    #Add taxcalc version to results
    vinfo = taxcalc._version.get_versions()
    results['taxcalc_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    results['dropq_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    binfo = btax._version.get_versions()
    results['btax_version'] = binfo['version'] + '.' +  binfo['full-revisionid'][:6]
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
    results['taxcalc_version'] = vinfo['version'] + '.' + vinfo['full'][:6]
    dqvinfo = taxcalc.dropq._version.get_versions()
    results['dropq_version'] = vinfo['version'] + '.' + dqvinfo['full'][:6]

    #ogusa uses different version convention
    ogvinfo = ogusa._version.get_versions()
    ogusa_version = ".".join([ogvinfo['version'], ogvinfo['full-revisionid'][:6]])
    results['ogusa_version'] = ogusa_version
    json_res = json.dumps(results)
    return json_res
