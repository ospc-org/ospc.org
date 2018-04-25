import mock
import json

from django.test import TestCase
from django.test import Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test.client import RequestFactory

from .. import compute
from ..compute import DropqCompute, MockCompute
from ...test_assets import *
import requests_mock


class MockComputeTests(MockCompute):

    def remote_submit_job(self, theurl, data, timeout):
        assert "first_budget_year" in list(data.keys())
        return super(MockComputeTests, self).remote_submit_job(theurl, data, timeout)


class ComputeTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.dropq_compute = MockComputeTests()
        # self.dropq_compute.remote_submit_job = MockCompute().remote_submit_job
        self.client = Client()

    def test_submit_calculation(self):
        reform_dict = {
            2018: {
                '_SS_Earnings_c': [400000],
                '_II_em_cpi': False,
                '_II_em': [8000]
            },
            2019: {
                '_SS_Earnings_c': [500000],
                '_ALD_InvInc_ec_rt': [0.2]},
            2020: {
                '_SS_Earnings_c': [600000],
                '_II_em_cpi': True
            }
        }
        assumptions_dict = {
            'growdiff_response': {},
            'consumption': {},
            'behavior': {},
            'growdiff_baseline': {}
        }
        user_mods = dict({'policy': reform_dict}, **assumptions_dict)
        data = {'user_mods': json.dumps(user_mods),
                'first_budget_year': 2016,
                'start_budget_year': 0,
                'num_budget_years': 9}
        self.dropq_compute.submit_calculation(
            data, 'http://{hn}/dropq_start_job'
        )
