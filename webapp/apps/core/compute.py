import os
import requests
import msgpack
from requests.exceptions import RequestException, Timeout
import requests_mock
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


class JobFailError(Exception):
    '''An Exception to raise when a remote jobs has failed'''


class Compute(object):
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
        return self.submit(data, url_template, increment_counter=False)

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
                jobs_done.append(job_response.text)
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

    def get_results(self, job_ids, job_failure=False):
        if job_failure:
            return self._get_results_base(job_ids, job_failure=job_failure)

        ans = self._get_results_base(job_ids, job_failure=job_failure)

        fields = ['renderable', 'download_only']
        results = {key: {} for key in fields}
        for x in fields:
            for result in ans:
                for name in result[x]:
                    results[x][name] = (results[x][name] if name in results[x]
                                        else '') + result[x][name]
        return results
