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


SUBMIT_DROPQ_DATA = {
    "mods": {2018: {u'_SS_Earnings_c': [400000], u'_II_em_cpi': False, u'_II_em': [8000]}, 2019: {u'_SS_Earnings_c': [500000], u'_ALD_InvInc_ec_rt': [0.2]}, 2020: {u'_SS_Earnings_c': [600000], u'_II_em_cpi': True}},
    "first_budget_year": 2013,
    "url_template": 'http://{hn}/dropq_start_job',
    "additional_data": {'growdiff_response': {}, 'consumption': {}, 'behavior': {}, 'growdiff_baseline': {}},
    "is_file": True
}


class MockComputeTests(MockCompute):

    def remote_submit_job(self, theurl, data, timeout):
        assert "first_budget_year" in data.keys()
        return super(MockComputeTests, self).remote_submit_job(theurl, data, timeout)


class ComputeTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.dropq_compute = MockComputeTests()
        # self.dropq_compute.remote_submit_job = MockCompute().remote_submit_job
        self.client = Client()

    def test_submit_calculation(self):
        self.dropq_compute.submit_calculation(
            SUBMIT_DROPQ_DATA["mods"],
            SUBMIT_DROPQ_DATA["first_budget_year"],
            SUBMIT_DROPQ_DATA["url_template"],
            num_years=1,
            additional_data=SUBMIT_DROPQ_DATA["additional_data"],
            pack_up_user_mods=False
        )
