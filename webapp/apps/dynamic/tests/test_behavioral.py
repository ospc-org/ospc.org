from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
import json
import pytest
# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute
import taxcalc
from taxcalc import Policy

from .utils import do_dynamic_sim, START_YEAR
from ...test_assets.utils import (check_posted_params, do_micro_sim,
                                  get_post_data, get_file_post_data,
                                  get_taxbrain_model)
from ..models import DynamicBehaviorOutputUrl
from ..forms import DynamicBehavioralInputsModelForm

CLIENT = Client()

@pytest.mark.usefixtures("r1")
@pytest.mark.django_db
class TestDynamicBehavioralViews(object):
    ''' Test the partial equilibrium dynamic views of this app. '''

    def test_behavioral_edit(self):
        # Do the microsim
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'II_em'] = [u'4333']

        micro1 = do_micro_sim(CLIENT, data)["response"]

        # Do another microsim
        data[u'II_em'] += [u'4334']
        micro2 = do_micro_sim(CLIENT, data)["response"]

        # Do a third microsim
        data[u'II_em'] += [u'4335']
        micro3 = do_micro_sim(CLIENT, data)["response"]

        # Do the partial equilibrium simulation based on the third microsim
        pe_reform = {u'BE_inc': [u'-0.4']}
        pe_response = do_dynamic_sim(CLIENT, 'behavioral', micro3, pe_reform)
        orig_micro_model_num = micro3.url[-2:-1]

        # Now edit this partial equilibrium sim
        # Go to behavioral input page
        behavior_num = pe_response.url[pe_response.url[:-1].rfind('/')+1:-1]
        dynamic_behavior_edit = '/dynamic/behavioral/edit/{0}/?start_year={1}'.format(behavior_num, START_YEAR)
        # load page
        response = CLIENT.get(dynamic_behavior_edit)
        assert response.status_code == 200
        page = response.content
        # Read the page to find the linked microsim. It should be the third
        # microsim above
        idx = page.find('dynamic/behavioral')
        idx_ms_num_start = idx + 19
        idx_ms_num_end = idx_ms_num_start + page[idx_ms_num_start:].find('/')
        microsim_model_num = page[idx_ms_num_start:idx_ms_num_end]
        microsim_url = page[idx:idx_ms_num_end]
        assert 'dynamic/behavioral/{0}'.format(microsim_model_num) == microsim_url

    def test_behavioral_reform_with_wildcard(self):
        # Do the microsim
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'SS_Earnings_c'] = [u'*,*,*,*,15000']

        micro1 = do_micro_sim(CLIENT, data)["response"]

        # Do the partial equilibrium simulation based on the microsim
        pe_reform = {u'BE_sub': [u'0.25']}
        pe_response = do_dynamic_sim(CLIENT, 'behavioral', micro1, pe_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        user_mods = json.loads(post['user_mods'])
        assert user_mods["policy"]["2020"][u'_SS_Earnings_c'][0]  == 15000.0
        assert user_mods["behavior"]["2016"]["_BE_sub"][0] == 0.25

    def test_behavioral_reform_post_gui(self):
        # Do the microsim
        start_year = u'2016'
        data = get_post_data(start_year)
        data[u'SS_Earnings_c'] = [u'*,*,*,*,15000']
        data['data_source'] = 'CPS'

        micro1 = do_micro_sim(CLIENT, data)["response"]

        # Do the partial equilibrium simulation based on the microsim
        pe_reform = {u'BE_sub': [u'0.25']}
        pe_response = do_dynamic_sim(CLIENT, 'behavioral', micro1,
                                     pe_reform, start_year=start_year)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        user_mods = json.loads(post['user_mods'])
        assert post["first_budget_year"] == int(start_year)
        assert user_mods["policy"]["2020"][u'_SS_Earnings_c'][0]  == 15000.0
        assert user_mods["behavior"]["2016"]["_BE_sub"][0] == 0.25
        assert post['use_puf_not_cps'] == False

    def test_behavioral_reform_from_file(self):
        # Do the microsim from file
        data = get_file_post_data(START_YEAR, self.r1)
        micro1 = do_micro_sim(CLIENT, data, post_url='/taxbrain/file/')
        micro1 = micro1["response"]

        # Do the partial equilibrium simulation based on the microsim
        be_reform = {u'BE_sub': [u'0.25']}
        be_response = do_dynamic_sim(CLIENT, 'behavioral', micro1, be_reform)
        orig_micro_model_num = micro1.url[-2:-1]
        from webapp.apps.dynamic import views
        post = views.dropq_compute.last_posted
        # Verify that partial equilibrium job submitted with proper
        # SS_Earnings_c with wildcards filled in properly
        user_mods = json.loads(post["user_mods"])
        assert post["first_budget_year"] == int(START_YEAR)
        assert user_mods["behavior"][str(START_YEAR)]["_BE_sub"][0] == 0.25

    def test_get_not_avail_page_renders(self):
        """
        Make sure not_avail.html page is rendered if exception is thrown
        while parsing results
        """
        start_year = 2018
        fields = get_post_data(start_year, _ID_BenefitSurtax_Switches=False)
        fields['BE_sub'] = ['0.25']
        fields["first_year"] = start_year
        unique_url = get_taxbrain_model(fields,
                                        first_year=start_year,
                                        taxcalc_vers="0.14.2",
                                        webapp_vers="1.3.0",
                                        Form=DynamicBehavioralInputsModelForm,
                                        UrlModel=DynamicBehaviorOutputUrl)

        model = unique_url.unique_inputs
        model.raw_input_fields = None
        model.input_fields = None
        model.deprecated_fields = None
        model.tax_result = "unrenderable"
        model.save()
        unique_url.unique_inputs = model
        unique_url.save()

        pk = unique_url.pk
        url = '/dynamic/behavior_results/{}/'.format(pk)
        response = CLIENT.get(url)
        assert any([t.name == 'taxbrain/not_avail.html'
                    for t in response.templates])
        edit_exp = '/dynamic/behavioral/edit/{}/?start_year={}'.format(
            pk,
            start_year
        )
        assert response.context['edit_href'] == edit_exp
