from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
import json
os.environ["NUM_BUDGET_YEARS"] = '2'

from ..models import TaxSaveInputs
from ..models import convert_to_floats
from ..compute import DropqCompute, MockCompute, ElasticMockCompute
import taxcalc
from taxcalc import Policy

START_YEAR = u'2016'

def do_micro_sim(client, reform):
    '''do the proper sequence of HTTP calls to run a microsim'''
    #Monkey patch to mock out running of compute jobs
    import sys
    from webapp.apps.taxbrain import views
    webapp_views = sys.modules['webapp.apps.taxbrain.views']
    webapp_views.dropq_compute = MockCompute()
    from webapp.apps.dynamic import views
    dynamic_views = sys.modules['webapp.apps.dynamic.views']
    dynamic_views.dropq_compute = MockCompute(num_times_to_wait=1)

    response = client.post('/taxbrain/', reform)
    # Check that redirect happens
    assert response.status_code == 302
    idx = response.url[:-1].rfind('/')
    assert response.url[:idx].endswith("taxbrain")
    return response


def check_posted_params(mock_compute, params_to_check, start_year):
    last_posted = mock_compute.last_posted
    user_mods = json.loads(last_posted["user_mods"])
    assert last_posted["first_budget_year"] == start_year
    print('check', params_to_check)
    print('user_mods', user_mods)
    for year in params_to_check:
        for param in params_to_check[year]:
            print(year, param)
            assert user_mods[str(year)][param] == params_to_check[year][param]


def file_to_dict_style(reform):
    dict_style = {}
    for param in reform:
        for year in reform[param]:
            if year in dict_style:
                dict_style[year][param] = reform[param][year]
            else:
                dict_style[year] = {param: reform[param][year]}

    return dict_style
