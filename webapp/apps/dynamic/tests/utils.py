from __future__ import print_function
from django.test import TestCase
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
import mock
import os
os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
from ..compute import MockDynamicCompute
import taxcalc
from taxcalc import Policy

from ...test_assets import *

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


def do_ogusa_sim(client, microsim_response, ogusa_reform, start_year,
                 increment=0, exp_status_code=302):

    import sys
    from webapp.apps.taxbrain import views
    webapp_views = sys.modules['webapp.apps.taxbrain.views']
    webapp_views.dropq_compute = MockCompute()
    from webapp.apps.dynamic import views
    dynamic_views = sys.modules['webapp.apps.dynamic.views']
    dynamic_views.dynamic_compute = MockDynamicCompute(increment=increment)

    # Go to the dynamic landing page
    idx = microsim_response.url[:-1].rfind('/')
    model_num = microsim_response.url[idx+1:-1]
    dynamic_landing = '/dynamic/{0}/?start_year={1}'.format(model_num, start_year)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to OGUSA input page
    dynamic_ogusa = '/dynamic/ogusa/{0}/?start_year={1}'.format(model_num, start_year)

    response = client.get(dynamic_ogusa)
    assert response.status_code == 200

    # Submit the OGUSA job submission
    response = client.post(dynamic_ogusa, ogusa_reform)
    assert response.status_code == exp_status_code
    return response
