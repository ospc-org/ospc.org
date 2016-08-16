import dropq
import os
from .helpers import package_up_vars
from ..taxbrain.models import WorkerNodesCounter
import json
import requests
from requests.exceptions import Timeout, RequestException
from .helpers import arrange_totals_by_row
from ..taxbrain.compute import DropqCompute, MockCompute, MockFailedCompute
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
ELASTIC_RESULTS_TOTAL_ROW_KEYS = ["gdp_elasticity"]

not_implement = 'This cls needs to be filled out like DropqCompute in ..taxbrain'
class JobFailError(Exception):
    '''An Exception to raise when a remote jobs has failed'''
    pass

class DropqBtaxMixin(object):
    num_budget_years = 1
    def package_up_vars(self, user_mods, first_budget_year):
        # TODO - is first_budget_year important here?
        user_mods = {k: v for k, v in user_mods.iteritems()
                     if k.startswith(('btax_', 'start_year'))}
        user_mods = {k: (v[0] if hasattr(v, '__getitem__') else v)
                     for k, v in user_mods.iteritems()}
        return user_mods

    def dropq_get_results(self, job_ids):
        ans = self._get_results_base(job_ids)
        print 'dropq_get_results', ans
        return ans

class DropqComputeBtax(DropqBtaxMixin, DropqCompute):
    pass

class MockComputeBtax(DropqBtaxMixin, MockCompute):
    pass

class ElasticMockCompute(DropqBtaxMixin, MockComputeBtax):
    pass

class MockFailedCompute(DropqBtaxMixin, MockComputeBtax):
    pass

class NodeDownCompute(DropqBtaxMixin, MockComputeBtax):
    pass