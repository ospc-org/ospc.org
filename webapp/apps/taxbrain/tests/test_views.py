from django.test import TestCase
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory
import mock
import json
import pytest
import os

NUM_BUDGET_YEARS = int(os.environ.get("NUM_BUDGET_YEARS", "10"))

from ..models import TaxSaveInputs, OutputUrl, WorkerNodesCounter
from ..models import convert_to_floats
from ..helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                     format_csv, arrange_totals_by_row, default_taxcalc_data)
from ..compute import (DropqCompute, MockCompute, MockFailedCompute,
                       NodeDownCompute)
from ..views import get_result_context
import taxcalc
from taxcalc import Policy

from ...test_assets import test_reform, test_assumptions
from ...test_assets.utils import (check_posted_params, do_micro_sim,
                                  get_post_data, get_file_post_data,
                                  get_dropq_compute_from_module,
                                  get_taxbrain_model)


START_YEAR = 2016

class TaxBrainViewsTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_taxbrain_get(self):
        # Issue a GET request.
        response = self.client.get('/taxbrain/')

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_taxbrain_post(self):
        """
        submit simple reform
        """
        data = get_post_data(START_YEAR)
        data[u'II_em'] = [u'4333']
        do_micro_sim(self.client, data)

    def test_taxbrain_quick_calc_post(self):
        "Test quick calculation post and full post from quick_calc page"
        # switches 0, 4, 6 are False
        data = get_post_data(START_YEAR, quick_calc=True)
        del data[u'ID_BenefitSurtax_Switch_0']
        del data[u'ID_BenefitSurtax_Switch_4']
        del data[u'ID_BenefitSurtax_Switch_6']
        data[u'II_em'] = [u'4333']

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        current_dropq_worker_offset = wnc.current_offset

        result = do_micro_sim(self.client, data, compute_count=1)

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        next_dropq_worker_offset = wnc.current_offset

        # Check that quick calc does not advance the counter
        self.assertEqual(current_dropq_worker_offset, next_dropq_worker_offset)

        # Check that data was saved properly
        truth_mods = {START_YEAR: {"_ID_BenefitSurtax_Switch":
                                   [[0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 0.0]],
                                   "_II_em": [4333.0]}
                      }
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(START_YEAR))

        # reset worker node count without clearing MockCompute session
        result['tb_dropq_compute'].reset_count()
        post_url = '/taxbrain/submit/{0}/'.format(result['pk'])
        submit_data = {'csrfmiddlewaretoken':'abc123'}

        result = do_micro_sim(
            self.client,
            submit_data,
            compute_count=NUM_BUDGET_YEARS,
            post_url=post_url
        )

        # Check that data was saved properly
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(START_YEAR))


    def test_taxbrain_file_post_quick_calc(self):
        """
        Using file-upload interface, test quick calculation post and full
        post from quick_calc page
        """
        data = get_file_post_data(START_YEAR, test_reform.reform_text, quick_calc=False)

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        current_dropq_worker_offset = wnc.current_offset

        post_url = '/taxbrain/file/'

        result = do_micro_sim(
            self.client,
            data,
            compute_count=1,
            post_url=post_url
        )

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        next_dropq_worker_offset = wnc.current_offset

        # Check that quick calc does not advance the counter
        self.assertEqual(current_dropq_worker_offset, next_dropq_worker_offset)

        # Check that data was saved properly
        truth_mods = taxcalc.Calculator.read_json_param_objects(
            test_reform.reform_text,
            None,
        )
        truth_mods = truth_mods["policy"]
        check_posted_params(result["tb_dropq_compute"], truth_mods,
                            str(START_YEAR))

        # reset worker node count without clearing MockCompute session
        result['tb_dropq_compute'].reset_count()
        post_url = '/taxbrain/submit/{0}/'.format(result['pk'])
        submit_data = {'csrfmiddlewaretoken':'abc123'}

        result = do_micro_sim(
            self.client,
            submit_data,
            compute_count=NUM_BUDGET_YEARS,
            post_url=post_url
        )

        # Check that data was saved properly
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(START_YEAR))


    def test_taxbrain_post_no_behavior_entries(self):
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        # Provide behavioral input
        data = get_post_data(START_YEAR)
        data[u'BE_inc'] = [u'0.1']

        response = self.client.post('/taxbrain/', data)
        # Check that we get a 400
        self.assertEqual(response.status_code, 400)


    def test_taxbrain_nodes_down(self):
        #Monkey patch to mock out running of compute jobs
        dropq_compute = get_dropq_compute_from_module(
            'webapp.apps.taxbrain.views',
            MockComputeObj=NodeDownCompute
        )

        data = get_post_data(START_YEAR)
        data[u'II_em'] = [u'4333']

        result = do_micro_sim(
            self.client,
            data,
            tb_dropq_compute=dropq_compute
        )

        # Check that data was saved properly
        truth_mods = {START_YEAR: {"_ID_BenefitSurtax_Switch":
                                   [[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]],
                                   "_II_em": [4333.0]}
                      }
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(START_YEAR))


    def test_taxbrain_failed_job(self):
        #Monkey patch to mock out running of compute jobs
        dropq_compute = get_dropq_compute_from_module(
            'webapp.apps.taxbrain.views',
            MockComputeObj=MockFailedCompute
        )

        data = get_post_data(START_YEAR)
        data[u'II_em'] = [u'4333']

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        response = self.client.get(response.url)
        # Make sure the failure message is in the response
        self.failUnless("Your calculation failed" in str(response))

    @pytest.mark.xfail
    def test_taxbrain_has_growth_params(self):

        reform = {'factor_adjustment': [u'0.03'],
                  'FICA_ss_trt': [u'0.11'],
                  'start_year': unicode(START_YEAR),
                  'has_errors': [u'False'],
                  'growth_choice': u'factor_adjustment'
                  }
        do_micro_sim(self.client, reform)


    def test_taxbrain_edit_cpi_flags_show_correctly(self):

        data = get_post_data(START_YEAR)
        data[u'II_em'] = [u'4333']
        data[u'AMT_CG_brk2_cpi'] = u'False'

        result = do_micro_sim(self.client, data)
        edit_micro = '/taxbrain/edit/{0}/?start_year={1}'.format(result["pk"],
                                                                 START_YEAR)
        edit_page = self.client.get(edit_micro)
        self.assertEqual(edit_page.status_code, 200)
        cpi_flag = edit_page.context['form']['AMT_CG_brk2_cpi'].field.widget.attrs['placeholder']
        self.assertEqual(cpi_flag, False)



    def test_taxbrain_edit_benefitsurtax_switch_show_correctly(self):
        # This post has no BenefitSurtax flags, so the model
        # sets them to False
        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        data[u'II_em'] = [u'4333']

        result = do_micro_sim(self.client, data)

        out = OutputUrl.objects.get(pk=result["pk"])
        tsi = TaxSaveInputs.objects.get(pk=out.model_pk)
        _ids = ['ID_BenefitSurtax_Switch_' + str(i) for i in range(7)]
        # Verify that generated model has switches all False
        assert all([(getattr(tsi, switch) == "False"
                     or getattr(tsi, switch) == u'0.0') for switch in _ids])
        # Now edit this page
        edit_micro = '/taxbrain/edit/{0}/?start_year={1}'.format(result["pk"],
                                                                 START_YEAR)
        edit_page = self.client.get(edit_micro)
        self.assertEqual(edit_page.status_code, 200)

        # Here we POST flipping two switches. The value of the post is
        # unimportant. The existence of the switch in the POST indicates
        # that the user set them to on. So, they must get switched to True
        next_csrf = str(edit_page.context['csrf_token'])
        data2 = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_em': [u'4333'],
               u'ID_BenefitSurtax_Switch_0': [u'False'],
               u'ID_BenefitSurtax_Switch_1': [u'False'],
               'csrfmiddlewaretoken': next_csrf}
        data2.update(mod)

        result2 = do_micro_sim(self.client, data2)

        out2 = OutputUrl.objects.get(pk=result2["pk"])
        tsi2 = TaxSaveInputs.objects.get(pk=out2.model_pk)
        assert (tsi2.ID_BenefitSurtax_Switch_0 == u'True'
                or tsi2.ID_BenefitSurtax_Switch_0 == u'1.0')
        assert (tsi2.ID_BenefitSurtax_Switch_1 == u'True'
                or tsi2.ID_BenefitSurtax_Switch_1 == u'1.0')
        assert (tsi2.ID_BenefitSurtax_Switch_2 == u'False'
                or tsi2.ID_BenefitSurtax_Switch_2 == u'0.0')
        assert (tsi2.ID_BenefitSurtax_Switch_3 == u'False'
                or tsi2.ID_BenefitSurtax_Switch_3 == u'0.0')
        assert (tsi2.ID_BenefitSurtax_Switch_4 == u'False'
                or tsi2.ID_BenefitSurtax_Switch_4 == u'0.0')
        assert (tsi2.ID_BenefitSurtax_Switch_5 == u'False'
                or tsi2.ID_BenefitSurtax_Switch_5 == u'0.0')
        assert (tsi2.ID_BenefitSurtax_Switch_6 == u'False'
                or tsi2.ID_BenefitSurtax_Switch_6 == u'0.0')


    def test_taxbrain_wildcard_params_with_validation_is_OK(self):
        """
        Set upper threshold for income tax bracket 1 to *, *, 38000
        income tax bracket 2 will inflate above 38000 so should give
        no error
        """
        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'*, *, 15000'],
               u'II_brk2_cpi': u'False'}
        data.update(mod)
        result = do_micro_sim(self.client, data)

        # Check that data was saved properly
        truth_mods = {
            START_YEAR: {'_II_brk2_cpi': False},
            START_YEAR + 2: {
                '_II_brk1': [[15000.0, 19069.63, 9534.81, 13650.38, 19069.63]]
            }
        }
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(START_YEAR))


    def test_taxbrain_wildcard_params_with_validation_gives_error(self):
        """
        Set upper threshold for income tax bracket 1 to *, *, 38000
        Set CPI flag for income tax bracket 2 to False
        In 2018, income tax bracket 2 will still be 37625 if CPI flag
        is false so should give an error
        """
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'*, *, 38000'],
               u'II_brk2_cpi': u'False'}
        data.update(mod)

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True


    def test_taxbrain_wildcard_in_validation_params_OK(self):
        """
        Set upper threshold for income tax bracket 1 to *, 38000
        Set upper threshold for income tax bracket 2 to *, *, 39500
        should be OK
        """
        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'*, *, 38000'],
               u'II_brk2_0': [u'*, *, 39500']}
        data.update(mod)
        do_micro_sim(self.client, data)


    def test_taxbrain_wildcard_in_validation_params_gives_error(self):
        """
        Set upper threshold for income tax bracket 1 to *, 38000
        Set upper threshold for income tax bracket 2 to *, *, 39500
        Set CPI flag for upper threshold for income tax brack to false
        so should give an error
        """
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'*, 38000'],
               u'II_brk2_0': [u'*, *, 39500'],
               u'II_brk2_cpi': u'False'}
        data.update(mod)

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True


    def test_taxbrain_rt_capital_gain_goes_to_amt(self):
        """
        Transfer over the regular tax capital gains to AMT
        """

        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {'CG_rt1': [0.25], 'CG_rt3': [u'0.25'], 'CG_rt2': [u'0.18'],
               'CG_brk1_cpi': [u'True'], 'CG_brk2_cpi': [u'True'],
               'CG_brk1_0': [u'38659'], 'CG_brk1_1': [u'76300'],
               'CG_brk1_2': [u'38650'], 'CG_brk1_3': [u'51400'],
               'CG_brk2_0': [u'425050'], 'CG_brk2_1': [u'476950'],
               'CG_brk2_2': [u'243475'], 'CG_brk2_3': [u'451000']}
        data.update(mod)

        result = do_micro_sim(self.client, data)

        out2 = OutputUrl.objects.get(pk=result["pk"])
        tsi2 = TaxSaveInputs.objects.get(pk=out2.model_pk)
        assert tsi2.CG_rt1 == u'0.25'
        assert tsi2.CG_rt2 == u'0.18'
        assert tsi2.CG_rt3 == u'0.25'
        assert tsi2.CG_brk1_cpi == True
        assert tsi2.CG_brk1_0 == u'38659'
        assert tsi2.CG_brk1_1 == u'76300'
        assert tsi2.CG_brk1_2 == u'38650'
        assert tsi2.CG_brk1_3 == u'51400'
        assert tsi2.CG_brk2_cpi == True
        assert tsi2.CG_brk2_0 == u'425050'
        assert tsi2.CG_brk2_1 == u'476950'
        assert tsi2.CG_brk2_2 == u'243475'
        assert tsi2.CG_brk2_3 == u'451000'

        assert tsi2.AMT_CG_rt1 == u'0.25'
        assert tsi2.AMT_CG_rt2 == u'0.18'
        assert tsi2.AMT_CG_rt3 == u'0.25'
        assert tsi2.AMT_CG_brk1_cpi == True
        assert tsi2.AMT_CG_brk1_0 == u'38659.0'
        assert tsi2.AMT_CG_brk1_1 == u'76300.0'
        assert tsi2.AMT_CG_brk1_2 == u'38650.0'
        assert tsi2.AMT_CG_brk1_3 == u'51400.0'
        assert tsi2.AMT_CG_brk2_cpi == True
        assert tsi2.AMT_CG_brk2_0 == u'425050.0'
        assert tsi2.AMT_CG_brk2_1 == u'476950.0'
        assert tsi2.AMT_CG_brk2_2 == u'243475.0'
        assert tsi2.AMT_CG_brk2_3 == u'451000.0'


    def test_taxbrain_rt_to_passthrough(self):
        """
        Transfer over the ind. income tax params to passthrough
        """
        values1 = {"II_brk1_0": [u'8750.'],
                   "II_brk1_1": [u'9200.'],
                   "II_brk1_2": [u'9350.'], "II_brk1_3": [u'9350.'],
                   "II_rt1": [0.09]}

        values2 = {"II_brk2_0": [u'36000.', u'38000.', u'40000.', u'41000.'],
                   "II_brk2_1": [u'72250.', u'74000.'],
                   "II_brk2_2": [u'36500.'], "II_brk2_3": [u'46500.'],
                   "II_rt2": [0.16]}

        values3 = {"II_brk3_0": [u'88000.'],
                   "II_brk3_1": [u'147000.'],
                   "II_brk3_2": [u'75000.'], "II_brk3_3": [u'126500.'],
                   "II_rt3": [0.23]}

        values4 = {"II_brk4_0": [u'184400.'],
                   "II_brk4_1": [u'224000.'],
                   "II_brk4_2": [u'112000.'], "II_brk4_3": [u'205000.'],
                   "II_rt4": [0.29]}

        values5 = {"II_brk5_0": [u'399000.'],
                   "II_brk5_1": [u'399500.'],
                   "II_brk5_2": [u'200000.'], "II_brk5_3": [u'405000.'],
                   "II_rt5": [0.31]}

        values6 = {"II_brk6_0": [u'403000.'],
                   "II_brk6_1": [u'453000.'],
                   "II_brk6_2": [u'252000.'], "II_brk6_3": [u'435000.'],
                   "II_rt6": [0.37]}

        values7 = {"II_brk7_0": [u'999999.'],
                   "II_brk7_1": [u'999999.'],
                   "II_brk7_2": [u'999999.'], "II_brk7_3": [u'999999.'],
                   "II_rt7": [0.42]}

        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)

        data.update(values1)
        data.update(values2)
        data.update(values3)
        data.update(values4)
        data.update(values5)
        data.update(values6)
        data.update(values7)
        #TODO: check how values are saved
        do_micro_sim(self.client, data)

    def test_taxbrain_file_post_only_reform(self):
        data = get_file_post_data(START_YEAR, test_reform.reform_text)
        do_micro_sim(self.client, data, post_url="/taxbrain/file/")


    def test_taxbrain_file_post_reform_and_assumptions(self):
        data = get_file_post_data(START_YEAR,
                                  test_reform.reform_text,
                                  test_assumptions.assumptions_text)

        do_micro_sim(self.client, data, post_url="/taxbrain/file/")


    def test_taxbrain_view_old_data_model(self):
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        unique_url = get_taxbrain_model(taxcalc_vers="0.10.0",
                                        webapp_vers="1.1.0")

        tsi = unique_url.unique_inputs
        old_result = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "example_old_result.json")

        with open(old_result) as f:
            tsi.tax_result = json.loads(f.read())
        tsi.first_year = 2016
        tsi.save()
        factory = RequestFactory()
        req = factory.get('/taxbrain/')
        url = '/taxbrain/42'

        # Assert we can make result tables from old data
        ans = get_result_context(tsi, req, url)
        assert ans


    def test_taxbrain_bad_expression(self):
        """
        POST a bad expression for a TaxBrain parameter and verify that
        it gives an error
        """
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_post_data(START_YEAR, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'XTOT*4500'],
               u'II_brk2_0': [u'*, *, 39500']}
        data.update(mod)

        response = self.client.post('/taxbrain/', data)
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True


    def test_taxbrain_error_reform_file(self):
        """
        POST a reform file that causes errors. See PB issue #630
        """
        from webapp.apps.taxbrain.models import JSONReformTaxCalculator as js

        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_file_post_data(START_YEAR, test_reform.bad_reform)

        #TODO: make sure still not allowed to submit on second submission
        response = self.client.post('/taxbrain/file/', data)
        # Check that no redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True
        msg = 'ERROR: value 9e+99 > max value 89239.88 for _II_brk2_4 for 2024'
        assert msg in response.context['errors']

        # get most recent object
        objects = js.objects.order_by('id')
        obj = objects[len(objects) - 1]

        next_token = str(response.context['csrf_token'])

        form_id = obj.id
        data2 = {
            'csrfmiddlewaretoken': next_token,
            'form_id': form_id,
            'has_errors': [u'True'],
            'start_year': START_YEAR
        }

        response = self.client.post('/taxbrain/file/', data2)
        assert response.status_code == 200


    def test_taxbrain_warning_reform_file(self):
        """
        POST a reform file that causes warnings and check that re-submission
        is allowed. See PB issue #630 and #761
        """
        from webapp.apps.taxbrain.models import JSONReformTaxCalculator as js
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_file_post_data(START_YEAR, test_reform.warning_reform)

        response = self.client.post('/taxbrain/file/', data)
        # Check that no redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True
        msg = 'WARNING: value 1073.53 < min value 7191.08 for 2023'
        assert msg in response.context['errors']

        # get most recent object
        objects = js.objects.order_by('id')
        obj = objects[len(objects) - 1]

        next_token = str(response.context['csrf_token'])

        form_id = obj.id
        data2 = {
            'csrfmiddlewaretoken': next_token,
            'form_id': form_id,
            'has_errors': [u'True'],
            'start_year': START_YEAR
        }

        result = do_micro_sim(self.client, data2, post_url='/taxbrain/file/')

        truth_mods = {
            2020: {
                "_STD":  [[1000, 13583.32, 6791.67, 10000.32, 13583.32]]
            }
        }
        check_posted_params(result['tb_dropq_compute'], truth_mods, START_YEAR)

    def test_taxbrain_reform_file_file_swap(self):
        """
        POST a reform file that causes warnings, swap files, and make sure
        swapped files are used. See PB issue #630 and #761
        """
        start_year = 2017
        from webapp.apps.taxbrain.models import JSONReformTaxCalculator as js
        #Monkey patch to mock out running of compute jobs
        get_dropq_compute_from_module('webapp.apps.taxbrain.views')

        data = get_file_post_data(start_year, test_reform.warning_reform)

        response = self.client.post('/taxbrain/file/', data)
        # Check that no redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True
        msg = 'WARNING: value 1073.53 < min value 7191.08 for 2023'
        assert msg in response.context['errors']

        # get most recent object
        objects = js.objects.order_by('id')
        obj = objects[len(objects) - 1]

        next_token = str(response.context['csrf_token'])

        form_id = obj.id
        data2 = {
            'csrfmiddlewaretoken': next_token,
            'form_id': form_id,
            'has_errors': [u'True'],
            'start_year': start_year
        }
        data_file = get_file_post_data(START_YEAR,
                                       test_reform.r1,
                                       test_assumptions.assumptions_text)
        data2['docfile'] = data_file['docfile']
        data2['assumpfile'] = data_file['assumpfile']

        result = do_micro_sim(self.client, data2, post_url='/taxbrain/file/')

        dropq_compute = result['tb_dropq_compute']
        user_mods = json.loads(dropq_compute.last_posted["user_mods"])
        assert user_mods["behavior"][str(start_year)]["_BE_sub"][0] == 1.0
        truth_mods = {2018: {'_II_em': [8000.0]}}
        check_posted_params(dropq_compute, truth_mods, start_year)


    def test_taxbrain_up_to_2018(self):
        start_year = 2018
        data = get_post_data(start_year, _ID_BenefitSurtax_Switches=False)
        mod = {u'II_brk1_0': [u'*, *, 15000'],
               u'II_brk2_cpi': u'False'}
        data.update(mod)
        result = do_micro_sim(self.client, data)

        # Check that data was saved properly
        truth_mods = {
            start_year: {'_II_brk2_cpi': False},
        }
        check_posted_params(result['tb_dropq_compute'], truth_mods,
                            str(start_year))


    def test_taxbrain_file_up_to_2018(self):
        start_year = 2018
        data = get_file_post_data(start_year, test_reform.reform_text)

        post_url = '/taxbrain/file/'

        result = do_micro_sim(
            self.client,
            data,
            post_url=post_url
        )

        # Check that data was saved properly
        truth_mods = taxcalc.Calculator.read_json_param_objects(
            test_reform.reform_text,
            None,
        )
        truth_mods = truth_mods["policy"]
        check_posted_params(result["tb_dropq_compute"], truth_mods,
                            str(start_year))
