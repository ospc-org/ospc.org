import os
from .helpers import package_up_vars as _package_up_vars
from .models import WorkerNodesCounter
import json
import requests
import taxcalc
from requests.exceptions import Timeout, RequestException
from .helpers import arrange_totals_by_row
from ..constants import START_YEAR
import requests_mock
requests_mock.Mocker.TEST_PREFIX = 'dropq'

dqversion_info = taxcalc._version.get_versions()
dropq_version = dqversion_info['version']
NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
NUM_BUDGET_YEARS_QUICK = int(os.environ.get('NUM_BUDGET_YEARS_QUICK', 1))
#Hard fail on lack of dropq workers
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
DROPQ_URL = "/dropq_start_job"
# URL to perform the dropq algorithm on a sample of the full dataset
DROPQ_SMALL_URL = "/dropq_small_start_job"
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'
TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20
AGG_ROW_NAMES = taxcalc.tbi_utils.AGGR_ROW_NAMES
GDP_ELAST_ROW_NAMES = taxcalc.tbi.GDP_ELAST_ROW_NAMES


class JobFailError(Exception):
    '''An Exception to raise when a remote jobs has failed'''
    pass

class DropqCompute(object):

    num_budget_years = NUM_BUDGET_YEARS

    def package_up_vars(self, *args, **kwargs):
        return _package_up_vars(*args, **kwargs)


    def remote_submit_job(self, theurl, data, timeout=TIMEOUT_IN_SECONDS):
        print(theurl, data)
        response = requests.post(theurl, data=data, timeout=timeout)
        return response


    def remote_results_ready(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response


    def remote_retrieve_results(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response


    def submit_dropq_calculation(self, data):
        url_template = "http://{hn}" + DROPQ_URL
        return self.submit_calculation(data, url_template)


    def submit_dropq_small_calculation(self, data):
        url_template = "http://{hn}" + DROPQ_SMALL_URL
        return self.submit_calculation(data, url_template,
                                       increment_counter=False
                                       )


    def submit_elastic_calculation(self, data):
        url_template = "http://{hn}/elastic_gdp_start_job"
        return self.submit_calculation(data, url_template)


    def submit_calculation(self,
                           data,
                           url_template,
                           workers=DROPQ_WORKERS,
                           increment_counter=True,
                           use_wnc_offset=True):

        first_budget_year = int(data['first_budget_year'])
        start_budget_year = int(data['start_budget_year'])
        num_years = int(data['num_budget_years'])

        years = self._get_years(start_budget_year, num_years, first_budget_year)
        if use_wnc_offset:
            wnc, created = WorkerNodesCounter.objects.get_or_create(singleton_enforce=1)
            dropq_worker_offset = wnc.current_offset
            if dropq_worker_offset > len(workers):
                dropq_worker_offset = 0
            if increment_counter:
                wnc.current_offset = (dropq_worker_offset + num_years) % len(DROPQ_WORKERS)
                wnc.save()
        else:
            dropq_worker_offset = 0

        hostnames = workers[dropq_worker_offset: dropq_worker_offset + num_years]
        print "hostnames: ", hostnames
        num_hosts = len(hostnames)
        job_ids = []
        hostname_idx = 0
        max_queue_length = 0
        for y in years:
            year_submitted = False
            attempts = 0
            while not year_submitted:
                data['year'] = str(y)
                theurl = url_template.format(hn=hostnames[hostname_idx])
                try:
                    response = self.remote_submit_job(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
                    if response.status_code == 200:
                        print "submitted: ", hostnames[hostname_idx]
                        year_submitted = True
                        response_d = response.json()
                        job_ids.append((response_d['job_id'], hostnames[hostname_idx]))
                        hostname_idx = (hostname_idx + 1) % num_hosts
                        if response_d['qlength'] > max_queue_length:
                            max_queue_length = response_d['qlength']
                    else:
                        print "FAILED: ", str(y), hostnames[hostname_idx]
                        hostname_idx = (hostname_idx + 1) % num_hosts
                        attempts += 1
                except Timeout:
                    print "Couldn't submit to: ", hostnames[hostname_idx]
                    hostname_idx = (hostname_idx + 1) % num_hosts
                    attempts += 1
                except RequestException as re:
                    print "Something unexpected happened: ", re
                    hostname_idx = (hostname_idx + 1) % num_hosts
                    attempts += 1
                if attempts > MAX_ATTEMPTS_SUBMIT_JOB:
                    print "Exceeded max attempts. Bailing out."
                    raise IOError()

        return job_ids, max_queue_length

    def _get_years(self, start_budget_year, num_years, first_budget_year):
        if start_budget_year is not None:
            return list(range(start_budget_year, num_years))
        # The following is just a dummy year for btax
        # Btax is not currently running in separate years, I don't think.
        return [first_budget_year]

    def dropq_results_ready(self, job_ids):
        jobs_done = [None] * len(job_ids)
        for idx, id_hostname in enumerate(job_ids):
            id_, hostname = id_hostname
            result_url = "http://{hn}/dropq_query_result".format(hn=hostname)
            job_response = self.remote_results_ready(result_url, params={'job_id':id_})
            msg = '{0} failed on host: {1}'.format(id_, hostname)
            if job_response.status_code == 200: # Valid response
                rep = job_response.text
                jobs_done[idx] = rep
            else:
                print 'did not expect response with status_code', job_response.status_code
                raise JobFailError(msg)
        return jobs_done

    def _get_results_base(self, job_ids, job_failure=False):
        ans = []
        for idx, id_hostname in enumerate(job_ids):
            id_, hostname = id_hostname
            result_url = "http://{hn}/dropq_get_result".format(hn=hostname)
            job_response = self.remote_retrieve_results(result_url, params={'job_id':id_})
            if job_response.status_code == 200: # Valid response
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

        names = ["dist2_xdec", "dist1_xdec", "diff_itax_xdec", "diff_ptax_xdec",
                 "diff_comb_xdec", "dist2_xbin", "dist1_xbin", "diff_itax_xbin",
                 "diff_itax_xbin", "diff_ptax_xbin", "diff_comb_xbin", "aggr_d",
                 "aggr_1", "aggr_2"]
        results = {name: {} for name in names}

        for result in ans:
            for name in results:
                results[name].update(result[name])

        if ENFORCE_REMOTE_VERSION_CHECK:
            versions = [r.get('taxcalc_version', None) for r in ans]
            if not all([ver==taxcalc_version for ver in versions]):
                msg ="Got different taxcalc versions from workers. Bailing out"
                print msg
                raise IOError(msg)
            versions = [r.get('dropq_version', None) for r in ans]
            if not all([same_version(ver, dropq_version) for ver in versions]):
                msg ="Got different dropq versions from workers. Bailing out"
                print msg
                raise IOError(msg)

        results['aggr_d'] = arrange_totals_by_row(results['aggr_d'],
                                                  AGG_ROW_NAMES)

        results['aggr_1'] = arrange_totals_by_row(results['aggr_1'],
                                                  AGG_ROW_NAMES)

        results['aggr_2'] = arrange_totals_by_row(results['aggr_2'],
                                                  AGG_ROW_NAMES)

        return results

    def elastic_get_results(self, job_ids):
        ans = []
        for idx, id_hostname in enumerate(job_ids):
            id_, hostname = id_hostname
            result_url = "http://{hn}/dropq_get_result".format(hn=hostname)
            job_response = self.remote_retrieve_results(result_url, params={'job_id':id_})
            if job_response.status_code == 200: # Valid response
                ans.append(job_response.json())

        elasticity_gdp = {}
        for result in ans:
            elasticity_gdp.update(result['elasticity_gdp'])


        if ENFORCE_REMOTE_VERSION_CHECK:
            versions = [r.get('taxcalc_version', None) for r in ans]
            if not all([ver==taxcalc_version for ver in versions]):
                msg ="Got different taxcalc versions from workers. Bailing out"
                print msg
                raise IOError(msg)
            versions = [r.get('dropq_version', None) for r in ans]
            if not all([same_version(ver, dropq_version) for ver in versions]):
                msg ="Got different dropq versions from workers. Bailing out"
                print msg
                raise IOError(msg)

        elasticity_gdp[u'gdp_elasticity_0'] = u'NA'
        elasticity_gdp = arrange_totals_by_row(elasticity_gdp,
                                            GDP_ELAST_ROW_NAMES)

        results = {'elasticity_gdp': elasticity_gdp}

        return results


class MockCompute(DropqCompute):

    num_budget_years = NUM_BUDGET_YEARS
    __slots__ = ('count', 'num_times_to_wait', 'last_posted')

    def __init__(self, num_times_to_wait=0):
        self.count = 0
        # Number of times to respond 'No' before
        # replying that a job is ready
        self.num_times_to_wait = num_times_to_wait

    def remote_submit_job(self, theurl, data, timeout):
        with requests_mock.Mocker() as mock:
            resp = {'job_id': '424242', 'qlength':2}
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
        text = (u'{"elasticity_gdp": {"gdp_elasticity_1": "0.00310"}, '
                '"dropq_version": "0.6.a96303", "taxcalc_version": '
                '"0.6.10d462"}')
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_get_result', text=text)
            return DropqCompute.remote_retrieve_results(self, theurl, params)


class MockFailedCompute(MockCompute):

    def remote_results_ready(self, theurl, params):
        print 'MockFailedCompute remote_results_ready', theurl, params
        with requests_mock.Mocker() as mock:
            mock.register_uri('GET', '/dropq_query_result', text='FAIL')
            return DropqCompute.remote_results_ready(self, theurl, params)

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


    def remote_submit_job(self, theurl, data, timeout):
        with requests_mock.Mocker() as mock:
            resp = {'job_id': '424242', 'qlength':2}
            resp = json.dumps(resp)
            if (self.switch % 2 == 0):
                mock.register_uri('POST', DROPQ_URL, status_code=502)
                mock.register_uri('POST', '/elastic_gdp_start_job', status_code=502)
                mock.register_uri('POST', '/btax_start_job', status_code=502)
            else:
                mock.register_uri('POST', DROPQ_URL, text=resp)
                mock.register_uri('POST', '/elastic_gdp_start_job', text=resp)
                mock.register_uri('POST', '/btax_start_job', text=resp)
            self.switch += 1
            self.last_posted = data
            return DropqCompute.remote_submit_job(self, theurl, data, timeout)
