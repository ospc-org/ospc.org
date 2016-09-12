import dropq
import os
from ..taxbrain.models import WorkerNodesCounter
import json
import requests
from requests.exceptions import Timeout, RequestException
from .helpers import arrange_totals_by_row
from ..taxbrain.compute import (DropqCompute,
                                MockCompute,
                                MockFailedCompute,
                                NodeDownCompute,
                                JobFailError,
                                ENFORCE_REMOTE_VERSION_CHECK,
                                TIMEOUT_IN_SECONDS,
                                dropq_version)
import requests_mock
requests_mock.Mocker.TEST_PREFIX = 'dropq'
btax_workers = os.environ.get('BTAX_WORKERS', '')
BTAX_WORKERS = btax_workers.split(",")


def package_up_vars(self, user_mods, first_budget_year):
    # TODO - is first_budget_year important here?
    user_mods = {k: v for k, v in user_mods.iteritems()
                 if k.startswith(('btax_', 'start_year'))}
    user_mods = {k: (v[0] if hasattr(v, '__getitem__') else v)
                 for k, v in user_mods.iteritems()}
    return user_mods


def dropq_get_results(self, job_ids):
    ans = self._get_results_base(job_ids)
    return ans


class DropqComputeBtax(DropqCompute):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = dropq_get_results

    def submit_btax_calculation(self, mods, first_budget_year=2015):
        url_template = "http://{hn}/btax_start_job"
        return self.submit_calculation(mods, first_budget_year, url_template,
                                       start_budget_year=None, num_years=1,
                                       workers=BTAX_WORKERS,
                                       increment_counter=False,
                                       use_wnc_offset=False)


class MockComputeBtax(MockCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = dropq_get_results


class MockFailedComputeBtax(MockFailedCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = dropq_get_results


class NodeDownComputeBtax(NodeDownCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = dropq_get_results

