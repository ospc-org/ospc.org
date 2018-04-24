
from django.test import TestCase
from django.test import Client
from django.contrib.auth.models import User
import mock
import os
import pytest
import json
# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute
import taxcalc
from taxcalc import Policy

from ...dynamic.models import DynamicSaveInputs, OGUSAWorkerNodesCounter
from ..helpers import dynamic_params_from_model

START_YEAR = 2016

from .utils import do_ogusa_sim, START_YEAR
from ...test_assets.utils import (check_posted_params, do_micro_sim,
                                  get_post_data, get_file_post_data)
@pytest.mark.xfail
@pytest.mark.usefixtures("r1")
class DynamicOGUSAViewsTests(TestCase):
    ''' Test the ogusa dynamic views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary')


    def test_ogusa_different_start_years(self):
        self.client.login(username='temporary', password='temporary')
        # Do the microsim
        start_year = 2015
        data = get_post_data(start_year)

        # Do a 2015 microsim
        micro_2015 = do_micro_sim(self.client, data, dyn_dropq_compute=False)

        # Do the ogusa simulation based on this microsim
        ogusa_reform = {'frisch': ['0.42']}
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform, start_year)

        # Do a 2016 microsim
        start_year = 2016
        data['start_year'] = str(start_year)
        micro_2016 = do_micro_sim(self.client, data, dyn_dropq_compute=False)
        # Do the ogusa simulation based on this microsim
        ogusa_reform = {'frisch': ['0.43']}
        ogusa_response2 = do_ogusa_sim(self.client, micro_2016, ogusa_reform, start_year, increment=1)

        # Do a callback to say that the result is ready
        #self.client.get('/dynamic/dynamic_finished/?job_id=ogusa424243&status=SUCCESS')
        job_id = 'ogusa424243'
        qs = DynamicSaveInputs.objects.filter(job_ids__contains=job_id)
        dsi = qs[0]
        assert dsi.frisch == '0.43'
        assert dsi.first_year == 2016

    def test_ogusa_not_logged_in_no_email_fails(self):
        # Do the microsim
        start_year = 2015
        self.client.logout()
        data = get_post_data(start_year)

        # Do a 2015 microsim
        micro_2015 = do_micro_sim(self.client, data)

        # Do the ogusa simulation based on this microsim
        ogusa_reform = {'frisch': ['0.42']}
        ogusa_status_code = 403  # Should raise an error on no email address
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform,
                                      start_year, exp_status_code=ogusa_status_code)

        msg = 'Dynamic simulation must have an email address to send notification to!'
        assert ogusa_response["response"].content.decode('utf-8') == msg


    def test_ogusa_not_logged_with_email_succeeds(self):
        # Do the microsim
        start_year = 2015
        self.client.logout()
        data = get_post_data(start_year)

        # Do a 2015 microsim
        micro_2015 = do_micro_sim(self.client, data, dyn_dropq_compute=False)

        # Do the ogusa simulation based on this microsim
        ogusa_reform = {'frisch': ['0.42'], 'user_email': 'test@example.com'}
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform,
                                      start_year)


    def test_ogusa_with_params_show_up_in_email(self):
        # Do the microsim
        start_year = 2016
        self.client.logout()
        data = get_post_data(start_year)

        # Do a 2016 microsim
        micro_2016 = do_micro_sim(self.client, data, dyn_dropq_compute=False)

        # Do the ogusa simulation based on this microsim
        FRISCH_PARAM = '0.49'
        ogusa_reform = {'frisch': [FRISCH_PARAM], 'user_email': 'test@example.com'}
        ogusa_response = do_ogusa_sim(self.client, micro_2016, ogusa_reform,
                                      start_year)

        dsi = DynamicSaveInputs.objects.get(pk=ogusa_response["ogusa_pk"])
        ans = dynamic_params_from_model(dsi)
        assert ans['frisch'] == FRISCH_PARAM
        assert ans['g_y_annual'] == '0.03'


    @pytest.mark.django_db
    def test_ogusa_round_robins(self):
        # Do the microsim
        start_year = 2015
        self.client.login(username='temporary', password='temporary')

        import sys
        from webapp.apps.dynamic import helpers
        from webapp.apps.dynamic import compute
        # Monkey patch the variables we need to test
        helpers.OGUSA_WORKERS = ['host1', 'host2', 'host3']
        compute.OGUSA_WORKERS = ['host1', 'host2', 'host3']

        data = get_post_data(start_year)

        # Do a 2015 microsim
        micro_2015 = do_micro_sim(self.client, data, dyn_dropq_compute=False)

        #Assert the the worker node index has been reset to 0
        onc, created = OGUSAWorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        assert onc.current_idx == 0

        # Do the ogusa simulation based on this microsim
        ogusa_reform = {'frisch': ['0.42']}
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform,
                                      start_year)

        #Assert the the worker node index has incremented
        onc, created = OGUSAWorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        assert onc.current_idx == 1

        ogusa_reform = {'frisch': ['0.43']}
        ogusa_response = do_ogusa_sim(self.client, micro_2015, ogusa_reform,
                                      start_year)

        #Assert the the worker node index has incremented again
        onc, created = OGUSAWorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        assert onc.current_idx == 2

    def test_ogusa_reform_from_file(self):
        self.client.login(username='temporary', password='temporary')
        start_year = 2016
        # Do the microsim from file
        data = get_file_post_data(start_year, self.r1)
        micro1 = do_micro_sim(self.client, data, post_url='/taxbrain/file/')

        # Do the partial equilibrium simulation based on the microsim
        ogusa_reform = {'frisch': ['0.43']}
        ogusa_response = do_ogusa_sim(self.client, micro1, ogusa_reform,
                                      start_year)

        dsi = DynamicSaveInputs.objects.get(pk=ogusa_response["ogusa_pk"])
        ans = dynamic_params_from_model(dsi)
        assert ans['frisch'] == '0.43'
        assert ans['g_y_annual'] == '0.03'


    def test_static_parameters_saved(self):
        """
        Check that static parameters are saved as expected
        """
        self.client.login(username='temporary', password='temporary')
        start_year = 2017
        data = get_post_data(start_year)
        del data['ID_BenefitSurtax_Switch_0']
        del data['ID_BenefitSurtax_Switch_4']
        del data['ID_BenefitSurtax_Switch_6']
        data['II_em'] = ['4333']
        data['EITC_rt_0'] = ['1.2']
        data['ID_Charity_c_cpi'] = 'False'

        micro_sim = do_micro_sim(self.client, data, dyn_dropq_compute=False)
        ogusa_reform = {'frisch': ['0.42']}
        ogusa_sim = do_ogusa_sim(self.client, micro_sim, ogusa_reform, start_year)

        last_posted = ogusa_sim["ogusa_dropq_compute"].last_posted

        ogusa_params = json.loads(last_posted["ogusa_params"])
        assert ogusa_params["frisch"] == 0.42

        user_mods = json.loads(last_posted["user_mods"])
        reform = json.loads(user_mods['reform'])
        assert (
            reform["2017"]["_ID_BenefitSurtax_Switch"] == [[0.0, 1.0, 1.0, 1.0,
                                                            0.0, 1.0, 0.0]]
        )
        assert reform["2017"]['_II_em'] == [4333.0]
        assert reform["2017"]['_EITC_rt'][0][0] == 1.2
        assert reform["2017"]['_ID_Charity_c_cpi'] is False

        assump = json.loads(user_mods['assumptions'])
        assump_keys = ["growdiff_response", "consumption", "behavior",
                       "growdiff_baseline"]
        for assump_key in assump_keys:
            assert assump[assump_key] == {}
