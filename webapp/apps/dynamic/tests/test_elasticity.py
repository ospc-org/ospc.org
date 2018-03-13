from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
import json
import sys
# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
import taxcalc
from taxcalc import Policy

from .utils import do_dynamic_sim, START_YEAR
from ...test_assets.utils import (check_posted_params, do_micro_sim,
                                  get_post_data, get_file_post_data)


import pytest

@pytest.mark.usefixtures("r1")
class DynamicElasticityViewsTests(TestCase):
    ''' Test the elasticity of GDP dynamic views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_elasticity_edit(self):
        from webapp.apps.taxbrain import views
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

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

        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the elasticity of GDP simulation based on the third microsim
        egdp_reform = {u'elastic_gdp': [u'0.4']}
        egdp_response = do_dynamic_sim(self.client, 'macro', micro3, egdp_reform)
        orig_micro_model_num = micro3.url[-2:-1]

        # Now edit this elasticity of gdp sim
        # Go to macro input page
        egdp_num = egdp_response.url[egdp_response.url[:-1].rfind('/')+1:-1]
        dynamic_macro_edit = '/dynamic/macro/edit/{0}/?start_year={1}'.format(egdp_num, START_YEAR)
        # get edit page.
        response = self.client.get(dynamic_macro_edit)
        self.assertEqual(response.status_code, 200)
        page = response.content
        # Read the page to find the linked microsim. It should be the third
        # microsim above
        idx = page.find('dynamic/macro')
        idx_ms_num_start = idx + 14
        idx_ms_num_end = idx_ms_num_start + page[idx_ms_num_start:].find('/')
        microsim_model_num = page[idx_ms_num_start:idx_ms_num_end]
        microsim_url = page[idx:idx_ms_num_end]
        assert 'dynamic/macro/{0}'.format(microsim_model_num) == microsim_url

    def test_elasticity_cps(self):
        # Do the microsim
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'II_em'] = [u'4333']
        data['data_source'] = ['CPS']

        micro1 = do_micro_sim(self.client, data)

        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the elasticity of GDP simulation based on the third microsim
        egdp_reform = {u'elastic_gdp': [u'0.4']}
        egdp_response = do_dynamic_sim(self.client,'macro', micro1['response'],
                                          egdp_reform)
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted

        assert post['use_puf_not_cps'] == False

    @pytest.mark.xfail
    def test_elasticity_reform_from_file(self):
        # Do the microsim from file
        data = get_file_post_data(START_YEAR, self.r1)
        # set dyn_dropq_compute to False so that
        # webapp.apps.dynamic_views.dropq_compute is not Mocked
        micro1 = do_micro_sim(
            self.client,
            data,
            post_url='/taxbrain/file/',
            dyn_dropq_compute=False
        )

        micro1 = micro1["response"]

        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the partial equilibrium simulation based on the microsim
        el_reform = {u'elastic_gdp': [u'0.4']}
        el_response = do_dynamic_sim(self.client, 'macro', micro1, el_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        beh_params = json.loads(json.loads(post["behavior_params"])['elasticity_params'])
        assert beh_params["elastic_gdp"][0]  == 0.4
