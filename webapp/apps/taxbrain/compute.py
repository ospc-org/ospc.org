import os
import json
import requests
import msgpack
from requests.exceptions import RequestException, Timeout
import requests_mock
import taxcalc

requests_mock.Mocker.TEST_PREFIX = 'dropq'

NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
NUM_BUDGET_YEARS_QUICK = int(os.environ.get('NUM_BUDGET_YEARS_QUICK', 1))
WORKER_HN = os.environ.get('DROPQ_WORKERS')
DROPQ_URL = "/dropq_start_job"
# URL to perform the dropq algorithm on a sample of the full dataset
DROPQ_SMALL_URL = "/dropq_small_start_job"
TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20
BYTES_HEADER = {'Content-Type': 'application/octet-stream'}

from .helpers import arrange_totals_by_row
AGG_ROW_NAMES = taxcalc.tbi_utils.AGGR_ROW_NAMES
GDP_ELAST_ROW_NAMES = taxcalc.tbi.GDP_ELAST_ROW_NAMES

class JobFailError(Exception):
    '''An Exception to raise when a remote jobs has failed'''


class DropqCompute(object):
    num_budget_years = NUM_BUDGET_YEARS

    def remote_submit_job(
            self,
            theurl,
            data,
            timeout=TIMEOUT_IN_SECONDS,
            headers=None):
        print(theurl, data)
        if headers is not None:
            response = requests.post(theurl,
                                     data=data,
                                     timeout=timeout,
                                     headers=headers)
        else:
            response = requests.post(theurl, data=data, timeout=timeout)
        return response

    def remote_results_ready(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response

    def remote_retrieve_results(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response

    def submit_calculation(self, data):
        url_template = "http://{hn}" + DROPQ_URL
        return self.submit(data, url_template)

    def submit_quick_calculation(self, data):
        url_template = "http://{hn}" + DROPQ_SMALL_URL
        return self.submit(data, url_template,
                                       increment_counter=False
                                       )

    def submit_elastic_calculation(self, data):
        url_template = "http://{hn}/elastic_gdp_start_job"
        return self.submit(data, url_template)

    def submit(self,
                           data_list,
                           url_template,
                           increment_counter=True,
                           use_wnc_offset=True):

        print("hostnames: ", WORKER_HN)
        print("submitting data: ", data_list)
        job_ids = []
        queue_length = 0
        for data in data_list:
            submitted = False
            attempts = 0
            while not submitted:
                packed = msgpack.dumps({'inputs': data}, use_bin_type=True)
                theurl = url_template.format(hn=WORKER_HN)
                try:
                    response = self.remote_submit_job(
                        theurl, data=packed, timeout=TIMEOUT_IN_SECONDS,
                        headers=BYTES_HEADER)
                    if response.status_code == 200:
                        print("submitted: ", )
                        submitted = True
                        response_d = response.json()
                        job_ids.append(response_d['job_id'])
                        queue_length = response_d['qlength']
                    else:
                        print("FAILED: ", data, WORKER_HN)
                        attempts += 1
                except Timeout:
                    print("Couldn't submit to: ", WORKER_HN)
                    attempts += 1
                except RequestException as re:
                    print("Something unexpected happened: ", re)
                    attempts += 1
                if attempts > MAX_ATTEMPTS_SUBMIT_JOB:
                    print("Exceeded max attempts. Bailing out.")
                    raise IOError()

        return job_ids, queue_length

    def results_ready(self, job_ids):
        jobs_done = []
        for job_id in job_ids:
            result_url = "http://{hn}/dropq_query_result".format(hn=WORKER_HN)
            job_response = self.remote_results_ready(
                result_url, params={'job_id': job_id})
            msg = '{0} failed on host: {1}'.format(job_id, WORKER_HN)
            if job_response.status_code == 200:  # Valid response
                rep = job_response.text
                if rep == 'YES':
                    jobs_done.append('YES')
                else:
                    jobs_done.append('NO')
            else:
                print(
                    'did not expect response with status_code',
                    job_response.status_code)
                raise JobFailError(msg)
        return jobs_done

    def _get_results_base(self, job_ids, job_failure=False):
        ans = []
        for job_id in job_ids:
            result_url = "http://{hn}/dropq_get_result".format(hn=WORKER_HN)
            job_response = self.remote_retrieve_results(
                result_url,
                params={'job_id': job_id}
            )
            if job_response.status_code == 200:  # Valid response
                try:
                    if job_failure:
                        ans.append(job_response.text)
                    else:
                        ans.append(job_response.json())
                except ValueError:
                    # Got back a bad response. Get the text and re-raise
                    msg = 'PROBLEM WITH RESPONSE. TEXT RECEIVED: {}'
                    raise ValueError(msg)
        return ans

    def dropq_get_results(self, job_ids, job_failure=False):
        if job_failure:
            return self._get_results_base(job_ids, job_failure=job_failure)

        ans = self._get_results_base(job_ids, job_failure=job_failure)

        names = [
            "dist2_xdec",
            "dist1_xdec",
            "diff_itax_xdec",
            "diff_ptax_xdec",
            "diff_comb_xdec",
            "dist2_xbin",
            "dist1_xbin",
            "diff_itax_xbin",
            "diff_itax_xbin",
            "diff_ptax_xbin",
            "diff_comb_xbin",
            "aggr_d",
            "aggr_1",
            "aggr_2"]
        results = {name: {} for name in names}

        for result in ans:
            for name in results:
                results[name].update(result[name])

        # if ENFORCE_REMOTE_VERSION_CHECK:
        #     versions = [r.get('taxcalc_version', None) for r in ans]
        #     if not all([ver == taxcalc_version for ver in versions]):
        #         msg = ("Got different taxcalc versions from workers. "
        #                "Bailing out")
        #         print(msg)
        #         raise IOError(msg)
        #     versions = [r.get('dropq_version', None) for r in ans]
        #     if not all([same_version(ver, dropq_version) for ver in versions]):
        #         msg = "Got different dropq versions from workers. Bailing out"
        #         print(msg)
        #         raise IOError(msg)

        results['aggr_d'] = arrange_totals_by_row(results['aggr_d'],
                                                  AGG_ROW_NAMES)

        results['aggr_1'] = arrange_totals_by_row(results['aggr_1'],
                                                  AGG_ROW_NAMES)

        results['aggr_2'] = arrange_totals_by_row(results['aggr_2'],
                                                  AGG_ROW_NAMES)

        return results

    def eta(self, job_ids):
        return 10

class MockCompute(DropqCompute):

    num_budget_years = NUM_BUDGET_YEARS
    __slots__ = ('count', 'num_times_to_wait', 'last_posted')

    def __init__(self, num_times_to_wait=0):
        self.count = 0
        # Number of times to respond 'No' before
        # replying that a job is ready
        self.num_times_to_wait = num_times_to_wait

    def remote_submit_job(self, theurl, data, timeout, headers=None):
        with requests_mock.Mocker() as mock:
            resp = {'job_id': '424242', 'qlength': 2}
            resp = json.dumps(resp)
            mock.register_uri('POST', DROPQ_URL, text=resp)
            mock.register_uri('POST', DROPQ_SMALL_URL, text=resp)
            mock.register_uri('POST', '/elastic_gdp_start_job', text=resp)
            mock.register_uri('POST', '/btax_start_job', text=resp)
            self.last_posted = data
            return DropqCompute.remote_submit_job(self, theurl, data, timeout)

    def remote_results_ready(self, theurl, params):
        with requests_mock.Mocker() as mock:
            if self.num_times_to_wait > 0:
                mock.register_uri('GET', '/dropq_query_result', text='NO')
                self.num_times_to_wait -= 1
            else:
                mock.register_uri('GET', '/dropq_query_result', text='YES')
            return DropqCompute.remote_results_ready(self, theurl, params)

    def remote_retrieve_results(self, theurl, params):
        mock_path = os.path.join(os.path.split(__file__)[0], "tests",
                                 "response_year_{0}.json")
        with open(mock_path.format(self.count), 'r') as f:
            text = f.read()
        self.count += 1
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return DropqCompute.remote_retrieve_results(self, theurl, params)

    def reset_count(self):
        """
        reset worker node count
        """
        self.count = 0


class ElasticMockCompute(MockCompute):

    def remote_retrieve_results(self, theurl, params):
        self.count += 1
        text = ('{"elasticity_gdp": {"gdp_elasticity_1": "0.00310"}, '
                '"dropq_version": "0.6.a96303", "taxcalc_version": '
                '"0.6.10d462"}')
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return DropqCompute.remote_retrieve_results(self, theurl, params)


class MockFailedCompute(MockCompute):

    def remote_results_ready(self, theurl, params):
        print('MockFailedCompute remote_results_ready', theurl, params)
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_query_result', text='FAIL')
            return DropqCompute.remote_results_ready(self, theurl, params)


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
            resp = {'job_id': '424242', 'qlength': 2}
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
            return DropqCompute.remote_submit_job(self, theurl, data, timeout)
