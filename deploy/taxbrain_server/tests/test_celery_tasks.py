import contextlib
from functools import partial
import pickle
import sys

import pytest

import os
import json
import mock
import numpy as np
import numpy.testing as npt
import pandas as pd
from pandas import DataFrame, Series
import pytest

sys.path.append('..')
import celery_tasks as ct
import run_ogusa

TAXIO_JSON = {
  "policy": {
    "_AMT_brk1": # top of first AMT tax bracket
    {"2015": [200000],
     "2017": [300000],
    },
    "_EITC_c": # maximum EITC amount by number of qualifying kids (0,1,2,3+)
    {"2016": [[ 900, 5000,  8000,  9000]],
     "2019": [[1200, 7000, 10000, 12000]]
    },
    "_II_em": # personal exemption amount (see indexing changes below)
    {"2016": [6000],
     "2018": [7500],
     "2020": [9000]
    },
    "_II_em_cpi": # personal exemption amount indexing status
    {"2016": False, # values in future years are same as this year value
     "2018": True,   # values in future years indexed with this year as base
    },
    "_SS_Earnings_c": # social security (OASDI) maximum taxable earnings
    {"2016": [300000],
     "2018": [500000],
     "2020": [700000],
    },
    "_AMT_em_cpi": # AMT exemption amount indexing status
    {"2017": False, # values in future years are same as this year value
     "2020": True,   # values in future years indexed with this year as base
    }
  },
}

ASSUMPTIONS_JSON = {
  "title": "",
  "author": "",
  "date": "",
  "behavior": {
    "_BE_sub": {"2016": [0.25]}
  },
  "consumption": {
    "_MPC_e20400": {"2016": [0.01]}
  },
  "growdiff_response": {
  },
  "growdiff_baseline": {},
  "gdp_elasticity": {},
}


def btax_mock_data():
    with open('btax_example_output.pkl', 'rb') as f:
        return pickle.load(f)


@contextlib.contextmanager
def patch_taxcalc_dropq():
    old1 = ct.taxcalc.dropq.calculate_baseline_and_reform
    old2 = ct.taxcalc.dropq.groupby_means_and_comparisons
    old3 = ct.taxcalc.dropq.pd.DataFrame
    old4 = ct.taxcalc.dropq.create_json_table
    try:
        def do_nothing(n, *args, **kwargs):
            if n == 'as_dict':
                return {'abc': [1]}
            return tuple(mock.MagicMock() for _ in range(n))
        ct.taxcalc.dropq.calculate_baseline_and_reform = partial(do_nothing, 3)
        ct.taxcalc.dropq.groupby_means_and_comparisons = partial(do_nothing, 19)
        ct.taxcalc.dropq.pd.DataFrame = partial(do_nothing, 1)
        ct.taxcalc.dropq.create_json_table = partial(do_nothing, 'as_dict')
        yield True
    finally:
        ct.taxcalc.dropq.calculate_baseline_and_reform = old1
        ct.taxcalc.dropq.groupby_means_and_comparisons = old2
        ct.taxcalc.dropq.pd.DataFrame = old3
        ct.taxcalc.dropq.create_json_table = old4


def test_dropq_task():
    beh_params = {}
    year_n = 0
    first_budget_year = None
    user_mods = {'2016': {'_II_rt3': [0.31, 0.32, 0.33],
                          '_II_em_cpi': False,
                          '_II_rt4': [0.39, 0.4, 0.41]}}
    with patch_taxcalc_dropq() as _:
        result = ct.dropq_task_async.delay(year_n,
                                           user_mods,
                                           first_budget_year,
                                           beh_params)
    assert 'taxcalc_version' in result
    assert 'dropq_version' in result


@mock.patch('btax.execute.run_btax')
@mock.patch('celery_tasks.btax.front_end_util.add_summary_rows_and_breaklines')
def test_btax_async(summary, run_btax):
    summary.return_value = {'ok': 1}
    run_btax.return_value = btax_mock_data()
    user_mods = {"policy": {'_II_rt3': [0.31, 0.32, 0.33],
                            '_II_em_cpi': False,
                            '_II_rt4': [0.39, 0.4, 0.41]}}
    result = ct.btax_async.delay(user_mods)
    assert 'btax_version' in result


@contextlib.contextmanager
def patch_runner():
    old1 = run_ogusa.runner
    old2 = run_ogusa.postprocess.create_diff
    old3 = ct.taxcalc.dropq.format_macro_results
    try:
        def new(*args, **kwargs):
            return kwargs
        run_ogusa.runner = new
        run_ogusa.postprocess.create_diff = new
        ct.taxcalc.dropq.format_macro_results = new
        yield True

    finally:
        run_ogusa.runner = old1
        run_ogusa.postprocess.create_diff = old2
        ct.taxcalc.dropq.format_macro_results = old3


def test_ogusa_async():
    with patch_runner():
        user_mods = {'policy': {2016: {'_II_rt3': [0.31, 0.32, 0.33],
                                       '_II_em_cpi': False,
                                       '_II_rt4': [0.39, 0.4, 0.41]}}}
        user_mods = {"reform": json.dumps(TAXIO_JSON), "assumptions": json.dumps(ASSUMPTIONS_JSON)}
        ogusa_params = {'frisch': 0.44, 'g_y_annual': 0.021}
        guid = 'abc'
        result = ct.ogusa_async.delay(user_mods, ogusa_params, guid)
        assert 'ogusa_version' in result


@contextlib.contextmanager
def patch_mtr():
    old = ct.taxcalc.dropq.run_nth_year_gdp_elast_model
    try:
        def new(*args, **kwargs):
            return
        ct.taxcalc.dropq.run_nth_year_gdp_elast_model = new
        yield True
    finally:
        ct.taxcalc.dropq.run_nth_year_gdp_elast_model = old


def test_elasticity_gdp_task_async():
    with patch_mtr():
        first_budget_year, year = 2016, 0
        user_mods = {'policy': {2016: {'_II_rt3': [0.31, 0.32, 0.33],
                                       '_II_em_cpi': False,
                                       '_II_rt4': [0.39, 0.4, 0.41]}}}
        gdp_elasticity = dict(first_year=2018)
        user_mods = {"reform": json.dumps(TAXIO_JSON), "assumptions": json.dumps(ASSUMPTIONS_JSON)}
        result = ct.elasticity_gdp_task_async.delay(year, user_mods,
                                                    first_budget_year,
                                                    gdp_elasticity)
        assert 'elasticity_gdp' in result

