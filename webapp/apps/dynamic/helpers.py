import ogusa
import os
import requests
import taxcalc
import dropq
import sys
from ..taxbrain.helpers import TaxCalcParam

#
# General helpers
#

PYTHON_MAJOR_VERSION = sys.version_info.major


def string_to_float(x):
    return float(x.replace(',', ''))


def string_to_float_array(s):
    if len(s) > 0:
        return [float(x) for x in s.split(',')]
    else:
        return []


def same_version(v1, v2):
    idx = v1.rfind('.')
    return v1[:idx] == v2[:idx]


def arrange_totals_by_row(tots, keys):

    out = {}
    for key in keys:
        order_map = {}
        for name in tots:
            if name.startswith(key):
                year_num = int(name[name.rfind('_') + 1:])
                order_map[year_num] = tots[name]
        vals = [order_map[i] for i in range(len(order_map))]
        out[key] = vals
    return out

#
# Prepare user params to send to DropQ/Taxcalc
#

tcversion_info = taxcalc._version.get_versions()
ogversion_info = ogusa._version.get_versions()
ogusa_version = ".".join([ogversion_info['version'],
                         ogversion_info['full-revisionid'][:6]])

NUM_BUDGET_YEARS = int(os.environ.get('NUM_BUDGET_YEARS', 10))

TIMEOUT_IN_SECONDS = 1.0
MAX_ATTEMPTS_SUBMIT_JOB = 20

OGUSA_RESULTS_TABLE_LABELS = {
    'ogusa_tots': 'Macroeconomic Outputs',
}
TAXCALC_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.total_row_names
TAXCALC_RESULTS_TOTAL_ROW_KEY_LABELS = {
    'ind_tax': 'Individual Income Tax Liability Change',
    'payroll_tax': 'Payroll Tax Liability Change',
    'combined_tax': ('Combined Payroll and Individual Income '
                     'Tax Liability Change')
}


def convert_to_floats(tsi):
    """
    A helper function that tax all of the fields of a TaxSaveInputs model
    and converts them to floats, or list of floats
    """
    def numberfy_one(x):
        if isinstance(x, float):
            return x
        else:
            return float(x)

    def numberfy(x):
        if isinstance(x, list):
            return [numberfy_one(i) for i in x]
        else:
            return numberfy_one(x)

    attrs = vars(tsi)
    return {k: numberfy(v) for k, v in attrs.items() if v}


# Create a list of default parameters
def default_parameters(first_budget_year):

    # OGUSA_DEFAULT_PARAMS_JSON = ogusa.parameters.get_full_parameters()

    g_y_param = {'value': [0.03], 'cpi_inflated': False,
                 'col_label': ['Growth rate of tech.'],
                 'long_name': 'Growth rate of tech.',
                 'description': 'Annual growth rate of technology',
                 'irs_ref': '', 'notes': '', 'inflatable': False}

    upsilon_param = {'value': [3.0542], 'cpi_inflated': False,
                     'col_label': ['Omega'],
                     'long_name': 'omega for elliptical fit utility function',
                     'description': 'elliptical fit of utility function',
                     'irs_ref': '', 'notes': '', 'inflatable': False}

    # not using g_n or g_n_vector yet
    param_names_used = ['g_y_annual', 'upsilon']

    default_ogusa_params = {}
    # for p in param_names_used.iteritems():
    #    v = OGUSA_DEFAULT_PARAMS_JSON[p]
    #    param = TaxCalcParam(k,v, first_budget_year)
    #    default_taxcalc_params[param.nice_id] = param

    og_params = []
    og_params.append(('g_y_annual', g_y_param))
    og_params.append(('upsilon', upsilon_param))
    for k, v in og_params:
        param = TaxCalcParam(k, v, first_budget_year)
        default_ogusa_params[param.nice_id] = param

    return default_ogusa_params


# Debug TaxParams

def ogusa_results_to_tables(results, first_budget_year):
    """
    Take various results from dropq, i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display
    """
    return results


def submit_ogusa_calculation(mods, first_budget_year):
    print "mods is ", mods
    return [('a111', '1.1.1.1')]


# Might not be needed because this would be handled on the worker node side
def ogusa_results_ready(job_ids):
    jobs_done = [False] * len(job_ids)
    for idx, id_hostname in enumerate(job_ids):
        id_, hostname = id_hostname
        result_url = "http://{hn}/dropq_query_result".format(hn=hostname)
        job_response = requests.get(result_url, params={'job_id': id_})
        if job_response.status_code == 200: # Valid response
            rep = job_response.text
            if rep == 'YES':
                jobs_done[idx] = True
                print "got one!: ", id_

    return all(jobs_done)

def ogusa_get_results(job_ids):
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
