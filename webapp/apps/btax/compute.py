from functools import partial
import os
from ..core.compute import Compute
from ..taxbrain.mock_compute import (MockCompute,
                                     MockFailedCompute,
                                     NodeDownCompute,
                                     )
import requests_mock
requests_mock.Mocker.TEST_PREFIX = 'dropq'
btax_workers = os.environ.get('BTAX_WORKERS', '')
BTAX_WORKERS = btax_workers.split(",")


def package_up_vars(self, user_mods, first_budget_year):
    # TODO - is first_budget_year important here?
    user_mods = {k: v for k, v in user_mods.items()
                 if k.startswith(('btax_', 'start_year'))}
    user_mods = {k: (v[0] if hasattr(v, '__getitem__') else v)
                 for k, v in user_mods.items()}
    return user_mods


def mock_submit_calculation(self, *args, **kwargs):
    return (list(args), 1)


def mock_dropq_results_ready(arg, self, *args, **kwargs):
    return [arg]


def mock_dropq_get_results(is_error, self, *args, **kwargs):
    if is_error:
        ret = {0: 'Error expected in test'}
        return ret
    ret = {0: {'mY_dec': None,
               'mX_dec': None,
               'df_dec': None,
               'pdf_dec': None,
               'cdf_dec': None,
               'mY_bin': None,
               'mX_bin': None,
               'df_bin': None,
               'pdf_bin': None,
               'cdf_bin': None,
               'fiscal_tot_diffs': None,
               'fiscal_tot_base': None,
               'fiscal_tot_ref': None, }}
    return ret


class DropqComputeBtax(Compute):
    num_budget_years = 1
    package_up_vars = package_up_vars

    def submit_btax_calculation(self, user_mods, first_budget_year):
        url_template = "http://{hn}/btax_start_job"
        data = {}
        user_mods = self.package_up_vars(user_mods, first_budget_year)
        if not bool(user_mods):
            return False
        user_mods = {first_budget_year: user_mods}
        data['user_mods'] = user_mods
        data['start_year'] = int(first_budget_year)
        print('submitting btax data:', data)
        return self.submit([data], url_template,
                           increment_counter=False,
                           use_wnc_offset=False)

    def btax_get_results(self, job_ids, job_failure=False):
        return self._get_results_base(job_ids, job_failure=job_failure)


class MockComputeBtax(MockCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = partial(mock_dropq_get_results, 'YES')
    submit_calculation = mock_submit_calculation
    dropq_results_ready = partial(mock_dropq_results_ready, "YES")


class MockFailedComputeBtax(MockFailedCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = partial(mock_dropq_get_results, 'Failure message')
    submit_calculation = mock_submit_calculation
    dropq_results_ready = partial(mock_dropq_results_ready, "FAIL")


class NodeDownComputeBtax(NodeDownCompute, DropqComputeBtax):
    num_budget_years = 1
    package_up_vars = package_up_vars
    dropq_get_results = partial(mock_dropq_get_results, 'Failure message')
    submit_calculation = mock_submit_calculation
    dropq_results_ready = partial(mock_dropq_results_ready, "FAIL")
