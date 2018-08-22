from django.test import TestCase
from django.test import Client

from ..mock_compute import MockCompute


class MockComputeTests(MockCompute):

    def remote_submit_job(self, theurl, data, timeout, headers=None):
        return super(
            MockComputeTests,
            self).remote_submit_job(
            theurl,
            data,
            timeout,
            headers=headers)


class ComputeTests(TestCase):
    ''' Test the views of this app. '''

    def setUp(self):
        # Every test needs a client.
        self.dropq_compute = MockComputeTests()
        # self.dropq_compute.remote_submit_job = (MockCompute()
        #                                         .remote_submit_job)
        self.client = Client()

    def test_submit_calculation(self):
        data = {
            'param1': {'stuff': {'more stuff': 1, 2: 'other stuff'}},
            'param2': {'params': 'values'}
        }
        self.dropq_compute.submit(
            data, 'http://{hn}/dropq_start_job'
        )
