from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
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
    dynamic_views.dropq_compute = MockCompute(num_times_to_wait=2)

    response = client.post('/taxbrain/', reform)
    # Check that redirect happens
    assert response.status_code == 302
    assert response.url[:-2].endswith("taxbrain/")
    return response


def do_behavioral_sim(client, microsim_response, pe_reform):
    # Link to dynamic simulation
    model_num = microsim_response.url[-2:]
    dynamic_landing = '/dynamic/{0}?start_year={1}'.format(model_num, START_YEAR)
    response = client.get(dynamic_landing)
    assert response.status_code == 200

    # Go to behavioral input page
    dynamic_behavior = '/dynamic/behavioral/{0}?start_year={1}'.format(model_num, START_YEAR)
    response = client.get(dynamic_behavior)
    assert response.status_code == 200

    # Do the partial equilibrium job submission
    response = client.post(dynamic_behavior, pe_reform)
    assert response.status_code == 302

    print(response)
    assert response.url[:-2].endswith("processing/")

    #Check that we are not done processing
    not_ready_page = client.get(response.url)
    not_ready_page.status_code == 200

    #Check should get a redirect this time
    response = client.get(response.url)
    assert response.status_code == 302
    assert response.url[:-2].endswith("behavior_results/")
    return response


class DynamicBehavioralViewsTests(TestCase):
    ''' Test the partial equilibrium dynamic views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_behavioral_edit(self):
        # Do the microsim
        reform = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': u'2016', 'csrfmiddlewaretoken': 'abc123'}

        micro1 = do_micro_sim(self.client, reform)

        # Do another microsim
        reform[u'II_em'] += [u'4334']
        micro2 = do_micro_sim(self.client, reform)

        # Do a third microsim
        reform[u'II_em'] += [u'4335']
        micro3 = do_micro_sim(self.client, reform)

        # Do the partial equilibrium simulation based on the third microsim
        pe_reform = {u'BE_inc': [u'0.4']}
        pe_response = do_behavioral_sim(self.client, micro3, pe_reform)
        orig_micro_model_num = micro3.url[-2:-1]

        # Now edit this partial equilibrium sim
        # Go to behavioral input page
        behavior_num = pe_response.url[pe_response.url[:-1].rfind('/')+1:-1]
        dynamic_behavior_edit = '/dynamic/behavioral/edit/{0}?start_year={1}'.format(behavior_num, START_YEAR)
        #Redirect first
        response = self.client.get(dynamic_behavior_edit)
        self.assertEqual(response.status_code, 301)
        #Now load the page
        rep2 = self.client.get(response.url)
        page = rep2.content
        # Read the page to find the linked microsim. It should be the third
        # microsim above
        idx = page.find('dynamic/behavioral')
        idx_ms_num_start = idx + 19
        idx_ms_num_end = idx_ms_num_start + page[idx_ms_num_start:].find('/') 
        microsim_model_num = page[idx_ms_num_start:idx_ms_num_end]
        assert microsim_model_num == orig_micro_model_num

