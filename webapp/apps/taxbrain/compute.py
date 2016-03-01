import dropq
import os
from .helpers import package_up_vars
import json
import requests
from requests.exceptions import Timeout, RequestException
from .helpers import arrange_totals_by_row
import requests_mock
requests_mock.Mocker.TEST_PREFIX = 'dropq'

dqversion_info = dropq._version.get_versions()
dropq_version = ".".join([dqversion_info['version'], dqversion_info['full'][:6]])
NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))
START_YEAR = int(os.environ.get('START_YEAR', 2016))
#Hard fail on lack of dropq workers
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'
TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20
TAXCALC_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.total_row_names


class DropqCompute(object):

    def __init__(self):
        pass

    def remote_submit_job(self, theurl, data, timeout):
        import pdb;pdb.set_trace()
        response = requests.post(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
        return response

    def remote_results_ready(self, theurl, params):
        job_response = requests.get(thuerl, params=params)
        return job_response

    def remote_retrieve_results(self, theurl, params):
        job_response = requests.get(theurl, params=params)
        return job_response

    def submit_dropq_calculation(self, mods, first_budget_year):
        print "mods is ", mods
        user_mods = package_up_vars(mods, first_budget_year)
        if not bool(user_mods):
            return False
        print "user_mods is ", user_mods
        print "submit work"
        user_mods={first_budget_year:user_mods}
        years = list(range(0,NUM_BUDGET_YEARS))

        hostnames = DROPQ_WORKERS
        num_hosts = len(hostnames)
        data = {}
        data['user_mods'] = json.dumps(user_mods)
        job_ids = []
        hostname_idx = 0
        for y in years:
            year_submitted = False
            attempts = 0
            while not year_submitted:
                data['year'] = str(y)
                theurl = "http://{hn}/dropq_start_job".format(hn=hostnames[hostname_idx])
                try:
                    #response = requests.post(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
                    response = self.remote_submit_job(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
                    if response.status_code == 200:
                        print "submitted: ", str(y), hostnames[hostname_idx]
                        year_submitted = True
                        job_ids.append((response.text, hostnames[hostname_idx]))
                        hostname_idx = (hostname_idx + 1) % num_hosts
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

        return job_ids

    def dropq_results_ready(self, job_ids):
        jobs_done = [False] * len(job_ids)
        for idx, id_hostname in enumerate(job_ids):
            id_, hostname = id_hostname
            result_url = "http://{hn}/dropq_query_result".format(hn=hostname)
            job_response = requests.get(result_url, params={'job_id':id_})
            if job_response.status_code == 200: # Valid response
                rep = job_response.text
                if rep == 'YES':
                    jobs_done[idx] = True
                    print "got one!: ", id_

        return all(jobs_done)

    def dropq_get_results(self, job_ids):
        ans = []
        for idx, id_hostname in enumerate(job_ids):
            id_, hostname = id_hostname
            result_url = "http://{hn}/dropq_get_result".format(hn=hostname)
            job_response = requests.get(result_url, params={'job_id':id_})
            if job_response.status_code == 200: # Valid response
                ans.append(job_response.json())

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


@requests_mock.Mocker()
class MockCompute(DropqCompute):

    def __init__(self):
        pass

    def remote_submit_job(self, theurl, data, timeout, m):
        m.register_uri('POST', 'dropq_start_job', text='resp')
        return DropqCompute.remote_submit_job(self, theurl, data, timeout)

    def remote_results_ready(self, theurl, params, m):
        m.register_uri('GET', 'dropq_query_result', text='resp')
        return DropqCompute.remote_results_ready(self, theurl, params)

    def remote_retrieve_results(self, theurl, params, m):
        m.register_uri('GET', 'dropq_get_result', text='resp')
        return DropqCompute.remote_retrieve_results(self, theurl, params)

