import os
from ..taxbrain.helpers import package_up_vars, arrange_totals_by_row
import json
import requests
from requests.exceptions import Timeout, RequestException
import requests_mock
import taxcalc
from ..taxbrain.compute import DropqCompute, MockCompute
from .models import OGUSAWorkerNodesCounter
from .helpers import filter_ogusa_only
from ..constants import START_YEAR

dqversion_info = taxcalc._version.get_versions()
dropq_version = dqversion_info['version']
NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
#Hard fail on lack of dropq workers
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'
TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20
TAXCALC_RESULTS_TOTAL_ROW_KEYS = taxcalc.dropq.TOTAL_ROW_NAMES
ELASTIC_RESULTS_TOTAL_ROW_KEYS = ["gdp_elasticity"]
ogusa_workers = os.environ.get('OGUSA_WORKERS', '')
OGUSA_WORKERS = ogusa_workers.split(",")
CALLBACK_HOSTNAME = os.environ.get('CALLBACK_HOSTNAME', 'localhost:8000')
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'


class DynamicCompute(DropqCompute):

    def remote_register_job(self, theurl, data, timeout=TIMEOUT_IN_SECONDS):
        response = requests.post(theurl, data=data, timeout=timeout)
        return response

    def submit_ogusa_calculation(self, ogusa_mods, first_budget_year, microsim_data):
        print "mods is ", ogusa_mods
        ogusa_params = filter_ogusa_only(ogusa_mods)
        data = {}
        data['taxio_format'] = True
        data['first_budget_year'] = first_budget_year
        microsim_params = microsim_data


        print "submit dynamic work"

        hostnames = OGUSA_WORKERS

        DEFAULT_PARAMS = {
            'callback': "http://{}/dynamic/dynamic_finished".format(CALLBACK_HOSTNAME),
        }

        data['ogusa_params'] = json.dumps(ogusa_params)
        data['user_mods'] = json.dumps(microsim_params)
        data['first_year'] = first_budget_year
        job_ids = []
        guids = []

        onc, created = OGUSAWorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
        # Get the current value mod'd to the current worker set
        ogusa_worker_idx = onc.current_idx % len(OGUSA_WORKERS)
        # Increment for next time
        onc.current_idx = (ogusa_worker_idx + 1) % len(OGUSA_WORKERS)
        onc.save()
        hostname_idx = ogusa_worker_idx
        print "hostname_idx is", hostname_idx
        submitted = False
        registered = False
        attempts = 0
        while not submitted:
            theurl = "http://{hn}/ogusa_start_job".format(hn=hostnames[hostname_idx])
            try:
                response = self.remote_submit_job(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
                if response.status_code == 200:
                    print "submitted: ", hostnames[hostname_idx]
                    submitted = True
                    resp_data = json.loads(response.text)
                    job_ids.append((resp_data['job_id'], hostnames[hostname_idx]))
                    guids.append((resp_data['job_id'], resp_data.get('guid', 'None')))
                else:
                    print "FAILED: ", hostnames[hostname_idx]
                    attempts += 1
            except Timeout:
                print "Couldn't submit to: ", hostnames[hostname_idx]
                # Increment to next ogusa node
                onc.current_offset = (ogusa_worker_idx + 1) % len(OGUSA_WORKERS)
                onc.save()
                attempts += 1
            except RequestException as re:
                print "Something unexpected happened: ", re
                # Increment to next ogusa node
                onc.current_offset = (ogusa_worker_idx + 1) % len(OGUSA_WORKERS)
                onc.save()
                attempts += 1
            if attempts > MAX_ATTEMPTS_SUBMIT_JOB:
                print "Exceeded max attempts. Bailing out."
                # Increment to next ogusa node
                onc.current_offset = (ogusa_worker_idx + 1) % len(OGUSA_WORKERS)
                onc.save()
                raise IOError()

        params = DEFAULT_PARAMS.copy()
        params['job_id'] = job_ids[0]
        reg_url = "http://" + hostnames[hostname_idx] + "/register_job"

        while not registered:
            reg_url = "http://{hn}/register_job".format(hn=hostnames[hostname_idx])
            try:
                params = DEFAULT_PARAMS.copy()
                params['job_id'] = job_ids[0][0]
                reg_url = "http://" + hostnames[hostname_idx] + "/register_job"

                register = self.remote_register_job(reg_url, data=params, timeout=TIMEOUT_IN_SECONDS)
                if response.status_code == 200:
                    print "registered: ", hostnames[hostname_idx]
                    registered = True
                else:
                    print "FAILED: ", hostnames[hostname_idx]
                    attempts += 1
            except Timeout:
                print "Couldn't submit to: ", hostnames[hostname_idx]
                attempts += 1
            except RequestException as re:
                print "Something unexpected happened: ", re
                attempts += 1
            if attempts > MAX_ATTEMPTS_SUBMIT_JOB:
                print "Exceeded max attempts. Bailing out."
                raise IOError()

        return job_ids, guids

    def ogusa_get_results(self, job_ids, status):
        '''
        job_ids = celery ID and hostname of job
        status = either "SUCCESS" or "FAILURE"
        '''
        id_hostname  = job_ids[0]
        id_, hostname = id_hostname
        result_url = "http://{hn}/dropq_get_result".format(hn=hostname)
        job_response = self.remote_retrieve_results(result_url, params={'job_id':id_})
        if job_response.status_code == 200: # Valid response
            if status == "SUCCESS":
                response = job_response.json()
                df_ogusa = {}
                df_ogusa.update(response['df_ogusa'])
                results = {'df_ogusa': df_ogusa}
            elif status == "FAILURE":
                results = {'job_fail': job_response.text}
            else:
                raise ValueError("only know 'SUCCESS' or 'FAILURE' status")
        else:
            msg = "Don't know how to handle response: {0}"
            msg = msg.format(job_response.status_code)
            raise IOError(msg)

        if ENFORCE_REMOTE_VERSION_CHECK:
            versions = [r.get('ogusa_version', None) for r in ans]
            if not all([ver==ogusa_version for ver in versions]):
                msg ="Got different taxcalc versions from workers. Bailing out"
                print msg
                raise IOError(msg)
            versions = [r.get('dropq_version', None) for r in ans]
            if not all([same_version(ver, dropq_version) for ver in versions]):
                msg ="Got different dropq versions from workers. Bailing out"
                print msg
                raise IOError(msg)

        return results


class MockDynamicCompute(DynamicCompute):

    __slots__ = ('count', 'num_times_to_wait', 'increment')

    def __init__(self, **kwargs):
        if 'increment' in kwargs:
            self.increment = kwargs['increment']
            del kwargs['increment']
        else:
            self.increment = 0
        super(MockDynamicCompute, self).__init__(**kwargs)

    def remote_submit_job(self, theurl, data, timeout):
        with requests_mock.Mocker() as mock:
            job_id = 'ogusa' + str(424242 + self.increment)
            resp = {'job_id': job_id, 'guid': 'guia123456789'}
            resp = json.dumps(resp)
            mock.register_uri('POST', '/ogusa_start_job', text=resp)
            return DynamicCompute.remote_submit_job(self, theurl, data, timeout)

    def remote_register_job(self, theurl, data, timeout):
        with requests_mock.Mocker() as mock:
            resp = {'registered': 'guia123456789'}
            resp = json.dumps(resp)
            mock.register_uri('POST', '/register_job', text=resp)
            return DynamicCompute.remote_register_job(self, theurl, data, timeout)


    def remote_retrieve_results(self, theurl, params):
        mock_path = os.path.join(os.path.split(__file__)[0], "tests",
                                 "ogusa_results_0}.json")
        with open(mock_path.format(self.count), 'r') as f:
            text = f.read()
        self.count += 1
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return DynamicCompute.remote_retrieve_results(self, theurl, params)
