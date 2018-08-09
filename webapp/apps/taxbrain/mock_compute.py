import os
from ..core.compute import Compute, NUM_BUDGET_YEARS
import requests_mock
import json
from ..core.compute import DROPQ_URL, DROPQ_SMALL_URL

dummy_uuid = "42424200-0000-0000-0000-000000000000"

class MockCompute(Compute):

    num_budget_years = NUM_BUDGET_YEARS
    __slots__ = ('count', 'num_times_to_wait', 'last_posted')

    def __init__(self, num_times_to_wait=0):
        self.count = 0
        # Number of times to respond 'No' before
        # replying that a job is ready
        self.num_times_to_wait = num_times_to_wait

    def remote_submit_job(self, theurl, data, timeout, headers=None):
        with requests_mock.Mocker() as mock:
            resp = {'job_id': dummy_uuid, 'qlength': 2}
            resp = json.dumps(resp)
            mock.register_uri('POST', DROPQ_URL, text=resp)
            mock.register_uri('POST', DROPQ_SMALL_URL, text=resp)
            mock.register_uri('POST', '/elastic_gdp_start_job', text=resp)
            mock.register_uri('POST', '/btax_start_job', text=resp)
            self.last_posted = data
            return Compute.remote_submit_job(self, theurl, data, timeout)

    def remote_results_ready(self, theurl, params):
        with requests_mock.Mocker() as mock:
            if self.num_times_to_wait > 0:
                mock.register_uri('GET', '/dropq_query_result', text='NO')
                self.num_times_to_wait -= 1
            else:
                mock.register_uri('GET', '/dropq_query_result', text='YES')
            return Compute.remote_results_ready(self, theurl, params)

    def remote_retrieve_results(self, theurl, params):
        mock_path = os.path.join(os.path.split(__file__)[0], "tests",
                                 "distributed_response.json")
        with open(mock_path.format(self.count), 'r') as f:
            text = f.read()
        self.count += 1
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return Compute.remote_retrieve_results(self, theurl, params)

    def reset_count(self):
        """
        reset worker node count
        """
        self.count = 0


class MockFailedCompute(MockCompute):

    def remote_results_ready(self, theurl, params):
        print('MockFailedCompute remote_results_ready', theurl, params)
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_query_result', text='FAIL')
            return Compute.remote_results_ready(self, theurl, params)


class MockFailedComputeOnOldHost(MockCompute):
    """
    Simulate requesting results from a host IP that is no longer used. This
    action should raise a `ConnectionError`
    """

    def remote_results_ready(self, theurl, params):
        print('MockFailedComputeOnOldHost remote_results_ready',
              theurl, params)
        raise requests.ConnectionError()


class NodeDownCompute(MockCompute):

    __slots__ = ('count', 'num_times_to_wait', 'switch')

    def __init__(self, **kwargs):
        if 'switch' in kwargs:
            self.switch = kwargs['switch']
            del kwargs['switch']
        else:
            self.switch = 0
        self.count = 0
        self.num_times_to_wait = 0
        super(MockCompute, self).__init__(**kwargs)

    def remote_submit_job(self, theurl, data, timeout, headers=None):
        with requests_mock.Mocker() as mock:
            resp = {'job_id': dummy_uuid, 'qlength': 2}
            resp = json.dumps(resp)
            if (self.switch % 2 == 0):
                mock.register_uri('POST', DROPQ_URL, status_code=502)
                mock.register_uri(
                    'POST',
                    '/elastic_gdp_start_job',
                    status_code=502)
                mock.register_uri('POST', '/btax_start_job', status_code=502)
            else:
                mock.register_uri('POST', DROPQ_URL, text=resp)
                mock.register_uri('POST', '/elastic_gdp_start_job', text=resp)
                mock.register_uri('POST', '/btax_start_job', text=resp)
            self.switch += 1
            self.last_posted = data
            return Compute.remote_submit_job(self, theurl, data, timeout)
