from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
import json
os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
import taxcalc
from taxcalc import Policy
from .utils import *


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
        pe_reform = {u'BE_inc': [u'-0.4']}
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

    def test_behavioral_reform_with_wildcard(self):
        # Do the microsim
        reform = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'SS_Earnings_c': [u'*,*,*,*,1.0e99'],
                u'has_errors': [u'False'],
                u'start_year': u'2016', 'csrfmiddlewaretoken': 'abc123'}

        micro1 = do_micro_sim(self.client, reform)

        # Do the partial equilibrium simulation based on the microsim
        pe_reform = {u'BE_sub': [u'0.25']}
        pe_response = do_behavioral_sim(self.client, micro1, pe_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        reform = json.loads(post['user_mods'])
        assert reform["2016"][u'_SS_Earnings_c'][0]  == 118500.0

