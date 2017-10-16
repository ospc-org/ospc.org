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

from .utils import do_behavioral_sim, START_YEAR
from ...test_assets.utils import (check_posted_params, do_micro_sim,
                                  do_micro_sim_from_file, get_post_data,
                                  get_file_post_data)
from ...test_assets import test_reform, test_assumptions


class DynamicBehavioralViewsTests(TestCase):
    ''' Test the partial equilibrium dynamic views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_behavioral_edit(self):
        # Do the microsim
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'II_em'] = [u'4333']

        micro1 = do_micro_sim(self.client, data)["response"]

        # Do another microsim
        data[u'II_em'] += [u'4334']
        micro2 = do_micro_sim(self.client, data)["response"]

        # Do a third microsim
        data[u'II_em'] += [u'4335']
        micro3 = do_micro_sim(self.client, data)["response"]

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
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'SS_Earnings_c'] = [u'*,*,*,*,15000']

        micro1 = do_micro_sim(self.client, data)["response"]

        # Do the partial equilibrium simulation based on the microsim
        pe_reform = {u'BE_sub': [u'0.25']}
        pe_response = do_behavioral_sim(self.client, micro1, pe_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        reform = json.loads(post['user_mods'])
        assert reform["2020"][u'_SS_Earnings_c'][0]  == 15000.0


    def test_behavioral_reform_from_file(self):
        # Do the microsim from file
        micro1 = do_micro_sim_from_file(self.client, START_YEAR,
                                        test_reform.reform_text)

        # Do the partial equilibrium simulation based on the microsim
        be_reform = {u'BE_sub': [u'0.25']}
        be_response = do_behavioral_sim(self.client, micro1, be_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        beh_params = json.loads(post["behavior_params"])["behavior"]["2016"]
        assert beh_params["_BE_sub"][0] == 0.25
