from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
import sys
# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
from ..compute import MockDynamicCompute
import taxcalc
from taxcalc import Policy

from ...test_assets import *
from ...test_assets.utils import get_dropq_compute_from_module, do_micro_sim

START_YEAR = u'2016'


def do_behavioral_sim(client, microsim_response, pe_reform, start_year=START_YEAR):
    # Link to dynamic simulation
    model_num = microsim_response.url[-2:]
    dynamic_landing = '/dynamic/{0}?start_year={1}'.format(model_num, start_year)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to behavioral input page
    dynamic_behavior = '/dynamic/behavioral/{0}?start_year={1}'.format(model_num, start_year)
    response = client.get(dynamic_behavior)
    assert response.status_code == 200

    # Do the partial equilibrium job submission
    response = client.post(dynamic_behavior, pe_reform)
    assert response.status_code == 302
    print(response)

    # The results page will now succeed
    next_response = client.get(response.url)
    reload_count = 0
    while reload_count < 2:
        if next_response.status_code == 200:
            break
        elif next_response.status_code == 302:
            next_response = client.get(next_response.url)
            reload_count = 0
        else:
            raise RuntimeError("unable to load results page")

    assert response.url[:-2].endswith("behavior_results/")
    return response


def do_elasticity_sim(client, microsim_response, egdp_reform, start_year=START_YEAR):
    # Link to dynamic simulation
    model_num = microsim_response.url[-2:]
    dynamic_landing = '/dynamic/{0}?start_year={1}'.format(model_num, start_year)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to macro input page
    dynamic_egdp = '/dynamic/macro/{0}?start_year={1}'.format(model_num, start_year)
    response = client.get(dynamic_egdp)
    assert response.status_code == 200

    # Do the macro job submission
    response = client.post(dynamic_egdp, egdp_reform)
    assert response.status_code == 302
    print(response)

    # The results page will now succeed
    next_response = client.get(response.url)
    assert next_response.status_code == 200
    assert response.url[:-2].endswith("macro_results/")
    return response


def do_ogusa_sim(client, microsim_res, ogusa_reform, start_year,
                 increment=0, exp_status_code=302):
    """
    do the proper sequence of HTTP calls to run a dyanamic simulation

    microsim_res: dictionary of results from do_micro_sim
    dyn_dropq_compute: mocked dynamic dropq_compute object
    compute_count: number of jobs submitted; only checked in quick_calc tests
    post_url: url to post data; is also set to /taxbrain/file/ for file_input
              tests

    returns: response object, dynamic dropq compute object,
             primary key for model run, micro_sim result dictionary
    """

    # get mocked dynamic_compute object
    ogusa_dropq_compute = get_dropq_compute_from_module(
        'webapp.apps.dynamic.views',
        attr='dynamic_compute',
        MockComputeObj=MockDynamicCompute,
        increment=increment
    )

    # Go to the dynamic landing page
    dynamic_landing = '/dynamic/{0}/?start_year={1}'.format(microsim_res["pk"],
                                                            start_year)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to OGUSA input page
    dynamic_ogusa_temp = '/dynamic/ogusa/{0}/?start_year={1}'
    dynamic_ogusa = dynamic_ogusa_temp.format(microsim_res["pk"], start_year)

    response = client.get(dynamic_ogusa)
    assert response.status_code == 200

    # Submit the OGUSA job submission
    response = client.post(dynamic_ogusa, ogusa_reform)
    assert response.status_code == exp_status_code
    ogusa_pk = None
    idx = None
    if exp_status_code == 302:
        idx = response.url[:-1].rfind('/')
        ogusa_pk = response.url[idx+1:-1]

    return {"response": response,
            "ogusa_dropq_compute": ogusa_dropq_compute,
            "ogusa_pk": ogusa_pk,
            "microsim_res": microsim_res}
