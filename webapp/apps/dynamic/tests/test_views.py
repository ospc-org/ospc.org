from __future__ import print_function
from django.test import TestCase
from django.test import Client
import mock
import os
# os.environ["NUM_BUDGET_YEARS"] = '2'

from ...taxbrain.models import TaxSaveInputs
from ...taxbrain.models import convert_to_floats
from ...taxbrain.helpers import (expand_1D, expand_2D, expand_list, package_up_vars,
                                 format_csv, arrange_totals_by_row, default_taxcalc_data)
from ...taxbrain.compute import DropqCompute, MockCompute, ElasticMockCompute, MockFailedCompute
import taxcalc
from taxcalc import Policy

START_YEAR = u'2016'


class DynamicViewsTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.client = Client()

    def test_taxbrain_get(self):
        # Issue a GET request.
        response = self.client.get('/taxbrain/')

        # Check that the response is 200 OK.
        self.assertEqual(response.status_code, 200)

    def test_behavioral_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()
        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = MockCompute(num_times_to_wait=2)

        # Do the microsim
        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': u'2016', 'csrfmiddlewaretoken': 'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))

        # Link to dynamic simulation
        model_num = response.url[link_idx+1:-1]
        dynamic_landing = '/dynamic/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_landing)
        self.assertEqual(response.status_code, 200)

        # Go to behavioral input page
        dynamic_behavior = '/dynamic/behavioral/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_behavior)
        self.assertEqual(response.status_code, 200)

        # Do the partial equilibrium job submission
        pe_data = {u'BE_inc': [u'-0.4']}
        response = self.client.post(dynamic_behavior, pe_data)
        self.assertEqual(response.status_code, 302)
        print(response)

        #Check should get success this time
        response_success = self.client.get(response.url)
        self.assertEqual(response_success.status_code, 200)
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("behavior_results/"))


    def test_elastic_post(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()
        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        dynamic_views.dropq_compute = ElasticMockCompute(num_times_to_wait=1)

        # Do the microsim
        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': u'2016', 'csrfmiddlewaretoken': 'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))

        # Link to dynamic simulation
        model_num = response.url[link_idx+1:-1]
        dynamic_landing = '/dynamic/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_landing)
        self.assertEqual(response.status_code, 200)

        # Go to macro input page
        dynamic_egdp = '/dynamic/macro/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_egdp)
        self.assertEqual(response.status_code, 200)

        # Do the elasticity job submission
        el_data = {'elastic_gdp': [u'0.55']}
        response = self.client.post(dynamic_egdp, el_data)
        self.assertEqual(response.status_code, 302)
        print(response)

        #Check that we get success this time
        response_success = self.client.get(response.url)
        self.assertEqual(response_success.status_code, 200)
        self.failUnless(response.url[:-2].endswith("macro_results/"))

    def test_elastic_failed_job(self):
        #Monkey patch to mock out running of compute jobs
        import sys
        from webapp.apps.taxbrain import views
        webapp_views = sys.modules['webapp.apps.taxbrain.views']
        webapp_views.dropq_compute = MockCompute()
        from webapp.apps.dynamic import views
        dynamic_views = sys.modules['webapp.apps.dynamic.views']
        #dynamic_views.dropq_compute = ElasticFailedMockCompute(num_times_to_wait=1)
        dynamic_views.dropq_compute = MockFailedCompute(num_times_to_wait=1)

        # Do the microsim
        data = {u'ID_BenefitSurtax_Switch_1': [u'True'],
                u'ID_BenefitSurtax_Switch_0': [u'True'],
                u'ID_BenefitSurtax_Switch_3': [u'True'],
                u'ID_BenefitSurtax_Switch_2': [u'True'],
                u'ID_BenefitSurtax_Switch_5': [u'True'],
                u'ID_BenefitSurtax_Switch_4': [u'True'],
                u'ID_BenefitSurtax_Switch_6': [u'True'],
                u'has_errors': [u'False'], u'II_em': [u'4333'],
                u'start_year': u'2016', 'csrfmiddlewaretoken': 'abc123'}

        response = self.client.post('/taxbrain/', data)
        # Check that redirect happens
        self.assertEqual(response.status_code, 302)
        # Go to results page
        link_idx = response.url[:-1].rfind('/')
        self.failUnless(response.url[:link_idx+1].endswith("taxbrain/"))

        # Link to dynamic simulation
        model_num = response.url[link_idx+1:-1]
        dynamic_landing = '/dynamic/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_landing)
        self.assertEqual(response.status_code, 200)

        # Go to macro input page
        dynamic_egdp = '/dynamic/macro/{0}/?start_year={1}'.format(model_num, START_YEAR)
        response = self.client.get(dynamic_egdp)
        self.assertEqual(response.status_code, 200)

        # Do the elasticity job submission
        el_data = {'elastic_gdp': [u'0.55']}
        response = self.client.post(dynamic_egdp, el_data)
        self.assertEqual(response.status_code, 302)
        print(response)

        #Check that we get success this time
        response_success = self.client.get(response.url)
        self.assertEqual(response_success.status_code, 200)
        self.failUnless(response.url[:-2].endswith("macro_results/"))
        response = self.client.get(response.url)
        # Make sure the failure message is in the response
        self.failUnless("Your calculation failed" in str(response))
