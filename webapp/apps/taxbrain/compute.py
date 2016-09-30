import dropq
import os
from .helpers import package_up_vars as _package_up_vars
from .models import WorkerNodesCounter
import json
import requests
from requests.exceptions import Timeout, RequestException
from .helpers import arrange_totals_by_row
import requests_mock
requests_mock.Mocker.TEST_PREFIX = 'dropq'

dqversion_info = dropq._version.get_versions()
dropq_version = ".".join([dqversion_info['version'], dqversion_info['full'][:6]])
NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
NUM_BUDGET_YEARS_QUICK = int(os.environ.get('NUM_BUDGET_YEARS_QUICK', 1))
START_YEAR = int(os.environ.get('START_YEAR', 2016))
#Hard fail on lack of dropq workers
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
DROPQ_URL = "/dropq_start_job"
DROPQ_JSON_URL = "/dropq_json_start_job"
# URL to perform the dropq algorithm on a sample of the full dataset
DROPQ_SMALL_URL = "/dropq_small_start_job"
DROPQ_SMALL_JSON_URL = "/dropq_json_small_start_job"
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'
TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20
TAXCALC_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.total_row_names
ELASTIC_RESULTS_TOTAL_ROW_KEYS = ["gdp_elasticity"]


class JobFailError(Exception):
    '''An Exception to raise when a remote jobs has failed'''
    pass

class DropqCompute(object):

    num_budget_years = NUM_BUDGET_YEARS

    def __init__(self):
        pass

    # Override if needed, e.g. btax
    def package_up_vars(self, *args, **kwargs):
        return _package_up_vars(*args, **kwargs)

    def remote_submit_job(self, theurl, data, timeout=TIMEOUT_IN_SECONDS):
        response = requests.post(theurl, data=data, timeout=timeout)
        return response

    def remote_results_ready(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response

    def remote_retrieve_results(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response

    def submit_json_dropq_calculation(self, mods, first_budget_year):
        url_template = "http://{hn}" + DROPQ_URL
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       num_years=NUM_BUDGET_YEARS,
                                       pack_up_user_mods=False)

    def submit_dropq_calculation(self, mods, first_budget_year):
        url_template = "http://{hn}" + DROPQ_URL
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       num_years=NUM_BUDGET_YEARS)

    def submit_json_dropq_small_calculation(self, mods, first_budget_year):
        url_template = "http://{hn}" + DROPQ_SMALL_URL
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       num_years=NUM_BUDGET_YEARS_QUICK,
                                       increment_counter=False,
                                       pack_up_user_mods=False)

    def submit_dropq_small_calculation(self, mods, first_budget_year):
        url_template = "http://{hn}" + DROPQ_SMALL_URL
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       num_years=NUM_BUDGET_YEARS_QUICK,
                                       increment_counter=False)

    def submit_elastic_calculation(self, mods, first_budget_year):
        url_template = "http://{hn}/elastic_gdp_start_job"
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       start_budget_year=1)

    def submit_calculation(self, mods, first_budget_year, url_template,
                           start_budget_year=0, num_years=NUM_BUDGET_YEARS,
                           workers=DROPQ_WORKERS,
                           increment_counter=True,
                           use_wnc_offset=True,
                           pack_up_user_mods=True):
        print "mods is ", mods
        if pack_up_user_mods:
            user_mods = self.package_up_vars(mods, first_budget_year)
            if not bool(user_mods):
                return False
            print "user_mods is ", user_mods
            print "submit work"
            user_mods={first_budget_year:user_mods}
        else:
            user_mods = mods
            print "JSON user_mods is ", user_mods

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
        data = {}
        data['user_mods'] = json.dumps(user_mods)
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

        mY_dec = {}
        mX_dec = {}
        df_dec = {}
        pdf_dec = {}
        cdf_dec = {}
        mY_bin = {}
        mX_bin = {}
        df_bin = {}
        pdf_bin = {}
        cdf_bin = {}
        fiscal_tots = {}
        for result in ans:
            mY_dec.update(result['mY_dec'])
            mX_dec.update(result['mX_dec'])
            df_dec.update(result['df_dec'])
            pdf_dec.update(result['pdf_dec'])
            cdf_dec.update(result['cdf_dec'])
            mY_bin.update(result['mY_bin'])
            mX_bin.update(result['mX_bin'])
            df_bin.update(result['df_bin'])
            pdf_bin.update(result['pdf_bin'])
            cdf_bin.update(result['cdf_bin'])
            fiscal_tots.update(result['fiscal_tots'])


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

        fiscal_tots = arrange_totals_by_row(fiscal_tots,
                                            TAXCALC_RESULTS_TOTAL_ROW_KEYS)

        results = {'mY_dec': mY_dec, 'mX_dec': mX_dec, 'df_dec': df_dec,
                'pdf_dec': pdf_dec, 'cdf_dec': cdf_dec, 'mY_bin': mY_bin,
                'mX_bin': mX_bin, 'df_bin': df_bin, 'pdf_bin': pdf_bin,
                'cdf_bin': cdf_bin, 'fiscal_tots': fiscal_tots}

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
                                            ELASTIC_RESULTS_TOTAL_ROW_KEYS)

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
            return DropqCompute.remote_submit_job(self, theurl, data, timeout)
