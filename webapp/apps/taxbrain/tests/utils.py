from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
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
