from django.test import TestCase
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
import mock

from ..models import TaxSaveInputs, OutputUrl, WorkerNodesCounter
from ..models import convert_to_floats
from ..helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                     format_csv, arrange_totals_by_row, default_taxcalc_data)
from ..compute import (DropqCompute, MockCompute, MockFailedCompute,
                       NodeDownCompute)
import taxcalc
from taxcalc import Policy
from .utils import *

START_YEAR = 2016
JSON_SIMPLETAXIO_DATA = """
{
    "_AMT_tthd": // AMT taxinc threshold separating the two AMT tax brackets
    {"2015": [200000],
     "2017": [300000]
    },
    "_EITC_c": // maximum EITC amount by number of qualifying kids (0,1,2,3+)
    {"2016": [[ 900, 5000,  8000,  9000]],
     "2019": [[1200, 7000, 10000, 12000]]
    },
    "_II_em": // personal exemption amount (see indexing changes below)
    {"2016": [6000],
     "2018": [7500],
     "2020": [9000]
    },
    "_II_em_cpi": // personal exemption amount indexing status
    {"2016": false, // values in future years are same as this year value
     "2018": true   // values in future years indexed with this year as base
    },
    "_SS_Earnings_c": // social security (OASDI) maximum taxable earnings
    {"2016": [300000],
     "2018": [500000],
     "2020": [700000]
    },
    "_AMT_em_cpi": // AMT exemption amount indexing status
    {"2017": false, // values in future years are same as this year value
     "2020": true   // values in future years indexed with this year as base
    }
}
"""

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

        data = { u'has_errors': [u'False'], u'II_brk1_0': [u'*, 38000'],
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
        model_num = response.url[link_idx+1:-1]

        out2 = OutputUrl.objects.get(pk=model_num)
        tsi2 = TaxSaveInputs.objects.get(pk=out2.model_pk)
        assert tsi2.II_rt1 == u'0.09'
        assert tsi2.II_rt2 == u'0.16'
        assert tsi2.II_rt3 == u'0.23'
        assert tsi2.II_rt4 == u'0.29'
        assert tsi2.II_rt5 == u'0.31'
        assert tsi2.II_rt6 == u'0.37'
        assert tsi2.II_rt7 == u'0.42'
        assert tsi2.PT_rt1 == u'0.09'
        assert tsi2.PT_rt2 == u'0.16'
        assert tsi2.PT_rt3 == u'0.23'
        assert tsi2.PT_rt4 == u'0.29'
        assert tsi2.PT_rt5 == u'0.31'
        assert tsi2.PT_rt6 == u'0.37'
        assert tsi2.PT_rt7 == u'0.42'
        assert float(tsi2.PT_brk1_0) == float(tsi2.II_brk1_0)
        assert float(tsi2.PT_brk1_1) == float(tsi2.II_brk1_1)
        assert float(tsi2.PT_brk1_2) == float(tsi2.II_brk1_2)
        assert float(tsi2.PT_brk1_3) == float(tsi2.II_brk1_3)
        assert float(tsi2.PT_brk2_0) == float(tsi2.II_brk2_0)
        assert float(tsi2.PT_brk2_1) == float(tsi2.II_brk2_1)
        assert float(tsi2.PT_brk2_2) == float(tsi2.II_brk2_2)
        assert float(tsi2.PT_brk2_3) == float(tsi2.II_brk2_3)
        assert float(tsi2.PT_brk3_0) == float(tsi2.II_brk3_0)
        assert float(tsi2.PT_brk3_1) == float(tsi2.II_brk3_1)
        assert float(tsi2.PT_brk3_2) == float(tsi2.II_brk3_2)
        assert float(tsi2.PT_brk3_3) == float(tsi2.II_brk3_3)
        assert float(tsi2.PT_brk4_0) == float(tsi2.II_brk4_0)
        assert float(tsi2.PT_brk4_1) == float(tsi2.II_brk4_1)
        assert float(tsi2.PT_brk4_2) == float(tsi2.II_brk4_2)
        assert float(tsi2.PT_brk4_3) == float(tsi2.II_brk4_3)
        assert float(tsi2.PT_brk5_0) == float(tsi2.II_brk5_0)
        assert float(tsi2.PT_brk5_1) == float(tsi2.II_brk5_1)
        assert float(tsi2.PT_brk5_2) == float(tsi2.II_brk5_2)
        assert float(tsi2.PT_brk5_3) == float(tsi2.II_brk5_3)
        assert float(tsi2.PT_brk6_0) == float(tsi2.II_brk6_0)
        assert float(tsi2.PT_brk6_1) == float(tsi2.II_brk6_1)
        assert float(tsi2.PT_brk6_2) == float(tsi2.II_brk6_2)
        assert float(tsi2.PT_brk6_3) == float(tsi2.II_brk6_3)
        assert float(tsi2.PT_brk7_0) == float(tsi2.II_brk7_0)
        assert float(tsi2.PT_brk7_1) == float(tsi2.II_brk7_1)
        assert float(tsi2.PT_brk7_2) == float(tsi2.II_brk7_2)
        assert float(tsi2.PT_brk7_3) == float(tsi2.II_brk7_3)


    def test_taxbrain_json_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        tc_json = [unicode(JSON_SIMPLETAXIO_DATA)]
        data = {u'taxcalc': tc_json,
                u'has_errors': [u'False'], 
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123'}

        response = self.client.post('/taxbrain/json/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))


    def test_taxbrain_json_quick_calc_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()

        tc_json = [unicode(JSON_SIMPLETAXIO_DATA)]
        data = {u'taxcalc': tc_json,
                u'has_errors': [u'False'], 
                u'start_year': unicode(START_YEAR), 'csrfmiddlewaretoken':'abc123',
                u'quick_calc': 'Quick Calculation!'}

        response = self.client.post('/taxbrain/json/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))


    def test_taxbrain_file_post(self):
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


