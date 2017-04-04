from django.test import TestCase
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory
import mock
import json

from ..models import TaxSaveInputs, OutputUrl, WorkerNodesCounter
from ..models import convert_to_floats
from ..helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                     format_csv, arrange_totals_by_row, default_taxcalc_data)
from ..compute import (DropqCompute, MockCompute, MockFailedCompute,
                       NodeDownCompute)
from ..views import get_result_context
import taxcalc
from taxcalc import Policy
from .utils import *

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
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))


    def test_taxbrain_quick_calc_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123',
                u'quick_calc': 'Quick Calculation!'}

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        current_dropq_worker_offset = wnc.current_offset

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        response = self.client.get(response.url)
        # Check for good response
        self.assertEqual(response.status_code, 200)
        # Check that we only retrieve one year of results
        self.assertEqual(webapp_views.dropq_compute.count, 1)

        wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        next_dropq_worker_offset = wnc.current_offset
        # Check that quick calc does not advance the counter
        self.assertEqual(current_dropq_worker_offset, next_dropq_worker_offset)



    def test_taxbrain_post_no_behavior_entries(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        # Provide behavioral input
        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'BE_inc': [u'0.1'],
                u'start_year': unicode(START_YEAR)}

        response = self.client.post('/taxbrain/', data)
        # Check that we get a 400
        self.assertEqual(response.status_code, 400)

    def test_taxbrain_nodes_down(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = NodeDownCompute()

        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR),'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        # One more redirect
        response = self.client.get(response.url)
        # Check that we successfully load the page
        self.assertEqual(response.status_code, 200)

    def test_taxbrain_failed_job(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockFailedCompute()

        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        response = self.client.get(response.url)
        # Make sure the failure message is in the response
        self.failUnless("Your calculation failed" in str(response))

    def test_taxbrain_has_growth_params(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        reform = {'factor_adjustment': [u'0.03'],
                  'FICA_ss_trt': [u'0.11'],
                  'start_year': unicode(START_YEAR),
                  'has_errors': [u'False'],
                  'growth_choice': u'factor_adjustment'
                  }
        micro = do_micro_sim(self.client, reform)

    def test_taxbrain_edit_cpi_flags_show_correctly(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123', u'AMT_CG_brk2_cpi':u'False',
                u'AMT_CG_brk1_cpi':u'False'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        model_num = response.url[link_idx+1:-1]
        edit_micro = '/taxbrain/edit/{0}/?start_year={1}'.format(model_num, START_YEAR)
        edit_page = self.client.get(edit_micro)
        self.assertEqual(edit_page.status_code, 200)
        cpi_flag = edit_page.context['form']['AMT_CG_brk2_cpi'].field.widget.attrs['placeholder']
        self.assertEqual(cpi_flag, False)

    def test_taxbrain_edit_benefitsurtax_switch_show_correctly(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        # This post has no BenefitSurtax flags, so the model
        # sets them to False
        data = { u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        model_num = response.url[link_idx+1:-1]

        out = OutputUrl.objects.get(pk=model_num)
        tsi = TaxSaveInputs.objects.get(pk=out.model_pk)
        _ids = ['ID_BenefitSurtax_Switch_' + str(i) for i in range(7)]
        # Verify that generated model has switches all False
        assert all([(getattr(tsi, switch)) == "False" for switch in _ids])
        # Now edit this page
        edit_micro = '/taxbrain/edit/{0}/?start_year={1}'.format(model_num, START_YEAR)
        edit_page = self.client.get(edit_micro)
        self.assertEqual(edit_page.status_code, 200)

        # Here we POST flipping two switches. The value of the post is
        # unimportant. The existence of the switch in the POST indicates
        # that the user set them to on. So, they must get switched to True
        next_csrf = str(edit_page.context['csrf_token'])
        data2 = { u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':next_csrf,
                'ID_BenefitSurtax_Switch_0':[u'False'],
                'ID_BenefitSurtax_Switch_1':[u'False']}

        response = self.client.post('/taxbrain/', data2)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        model_num2 = response.url[link_idx+1:-1]

        out2 = OutputUrl.objects.get(pk=model_num2)
        tsi2 = TaxSaveInputs.objects.get(pk=out2.model_pk)
        assert tsi2.ID_BenefitSurtax_Switch_0 == u'True'
        assert tsi2.ID_BenefitSurtax_Switch_1 == u'True'
        assert tsi2.ID_BenefitSurtax_Switch_2 == u'False'
        assert tsi2.ID_BenefitSurtax_Switch_3 == u'False'
        assert tsi2.ID_BenefitSurtax_Switch_4 == u'False'
        assert tsi2.ID_BenefitSurtax_Switch_5 == u'False'
        assert tsi2.ID_BenefitSurtax_Switch_6 == u'False'


    def test_taxbrain_wildcard_params_with_validation_is_OK(self):
        """
        Set upper threshold for income tax bracket 1 to *, *, 38000
        income tax bracket 2 will inflate above 38000 so should give
        no error
        """
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'*, *, 15000'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123', u'II_brk2_cpi':u'False'}

        response = self.client.post('/taxbrain/', data)
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))


    def test_taxbrain_wildcard_params_with_validation_gives_error(self):
        """
        Set upper threshold for income tax bracket 1 to *, *, 38000
        Set CPI flag for income tax bracket 2 to False
        In 2018, income tax bracket 2 will still be 37625 if CPI flag
        is false so should give an error
        """
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'*, *, 38000'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123', u'II_brk2_cpi':u'False'}

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
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'*, *, 38000'],
                u'II_brk2_0': [u'*, *, 39500'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))

    def test_taxbrain_wildcard_in_validation_params_gives_error(self):
        """
        Set upper threshold for income tax bracket 1 to *, 38000
        Set upper threshold for income tax bracket 2 to *, *, 39500
        Set CPI flag for upper threshold for income tax brack to false
        so should give an error
        """
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'*, 38000'],
                u'II_brk2_0': [u'*, *, 39500'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123', u'II_brk2_cpi':u'False'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True

    def test_taxbrain_rt_capital_gain_goes_to_amt(self):
        """
        Transfer over the regular tax capital gains to AMT
        """
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = {'CG_rt1': [0.25], 'CG_rt3': [u'0.25'], 'CG_rt2': [u'0.18'],
                'CG_brk1_cpi': [u'True'], 'CG_brk2_cpi': [u'True'],
                'CG_brk1_0': [u'38659'], 'CG_brk1_1': [u'76300'],
                'CG_brk1_2': [u'38650'], 'CG_brk1_3': [u'51400'],
                'CG_brk2_0': [u'425050'], 'CG_brk2_1': [u'476950'],
                'CG_brk2_2': [u'243475'], 'CG_brk2_3': [u'451000'],
                'has_errors': [u'False'], u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)

        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))
        model_num = response.url[link_idx+1:-1]

        out2 = OutputUrl.objects.get(pk=model_num)
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
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()


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

        data = {'has_errors': [u'False'], u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123'}

        data.update(values1)
        data.update(values2)
        data.update(values3)
        data.update(values4)
        data.update(values5)
        data.update(values6)
        data.update(values7)

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)

        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))


    def test_taxbrain_file_post_only_reform(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()
        tc_file = SimpleUploadedFile("test_reform.json", "file_content")
        data = {u'docfile': tc_file,
                u'has_errors': [u'False'],
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/file/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))



    def test_taxbrain_file_post_reform_and_assumptions(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()
        tc_file = SimpleUploadedFile("test_reform.json", "file_content")
        tc_file2 = SimpleUploadedFile("test_assumptions.json", "file_content")
        data = {u'docfile': tc_file,
                u'assumpfile': tc_file2,
                u'has_errors': [u'False'],
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/file/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))

    def test_taxbrain_view_old_data_model(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        tsi = TaxSaveInputs()
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
        import sys
        from webapp.apps.taxbrain import views as webapp_views
        webapp_views.dropq_compute = MockCompute()

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'XTOT*4500'],
                u'II_brk2_0': [u'*, *, 39500'],
                u'start_year': unicode(START_YEAR),
                'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/', data)
        self.assertEqual(response.status_code, 200)
        assert response.context['has_errors'] is True
