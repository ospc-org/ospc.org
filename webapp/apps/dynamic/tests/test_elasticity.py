from django.test import Client
import pytest
import json
import sys
import msgpack

from ...taxbrain.mock_compute import MockCompute
from ..compute import ElasticMockCompute

from .utils import do_dynamic_sim, START_YEAR
from ...test_assets.utils import (do_micro_sim, get_post_data,
                                  get_file_post_data)


CLIENT = Client()


@pytest.mark.django_db
class TestDynamicElasticityViews(object):
    ''' Test the elasticity of GDP dynamic views of this app. '''

    def test_elasticity_edit(self):
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        # Do the microsim
        start_year = '2016'
        data = get_post_data(start_year)
        data['II_em'] = ['4333']

        do_micro_sim(CLIENT, data)

        # Do another microsim
        data['II_em'] += ['4334']
        do_micro_sim(CLIENT, data)

        # Do a third microsim
        data['II_em'] += ['4335']
        micro3 = do_micro_sim(CLIENT, data)["response"]

        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the elasticity of GDP simulation based on the third microsim
        egdp_reform = {'elastic_gdp': ['0.4']}
        egdp_response = do_dynamic_sim(
            CLIENT, 'macro', micro3, egdp_reform)
        orig_micro_model_num = micro3.url[-2:-1]

        # Now edit this elasticity of gdp sim
        # Go to macro input page
        egdp_num = egdp_response.url[egdp_response.url[:-1].rfind('/') + 1:-1]
        dynamic_macro_edit = '/dynamic/macro/edit/{0}/?start_year={1}'.format(
            egdp_num, START_YEAR)
        # get edit page.
        response = CLIENT.get(dynamic_macro_edit)
        assert response.status_code == 200
        page = response.content.decode('utf-8')
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
        start_year = '2016'
        data = get_post_data(start_year)
        data['II_em'] = ['4333']
        data['data_source'] = ['CPS']

        micro1 = do_micro_sim(CLIENT, data)

        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the elasticity of GDP simulation based on the third microsim
        egdp_reform = {'elastic_gdp': ['0.4']}
        egdp_response = do_dynamic_sim(CLIENT, 'macro',
                                       micro1['response'], egdp_reform)
        from webapp.apps.dynamic import views
        last_posted = views.dropq_compute.last_posted
        inputs = msgpack.loads(last_posted, encoding='utf8',
                               use_list=True)
        last_posted = inputs[0]
        assert last_posted['use_puf_not_cps'] is False

    @pytest.mark.xfail
    def test_elasticity_reform_from_file(self, r1):
        # Do the microsim from file
        data = get_file_post_data(START_YEAR, r1)
        # set dyn_dropq_compute to False so that
        # webapp.apps.dynamic_views.dropq_compute is not Mocked
        micro1 = do_micro_sim(
            CLIENT,
            data,
            post_url='/taxbrain/file/',
            dyn_dropq_compute=False
        )

        micro1 = micro1["response"]

        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the partial equilibrium simulation based on the microsim
        el_reform = {'elastic_gdp': ['0.4']}
        do_dynamic_sim(CLIENT, 'macro', micro1, el_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        beh_params = json.loads(
            json.loads(
                post["behavior_params"])['elasticity_params'])
        assert beh_params["elastic_gdp"][0] == 0.4
