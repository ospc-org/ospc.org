import ogusa
import os
import requests
import taxcalc
import dropq
import json
import sys
from ..taxbrain.helpers import TaxCalcParam
from .errors import JobFailureException, UnknownStatusException
from django.core.mail import send_mail
import requests
from requests.exceptions import Timeout, RequestException
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'

OGUSA_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.ogusa_row_names
OGUSA_RESULTS_TOTAL_ROW_KEY_LABELS = {n:n for n in OGUSA_RESULTS_TOTAL_ROW_KEYS}

OGUSA_RESULTS_TABLE_LABELS = {
    'df_ogusa': 'Difference between Base and User plan',
}

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



def filter_ogusa_only(user_values):

    unused_names = ['creation_date', '_state', 'id']

    for k, v in user_values.items():
        if k in unused_names:
            print "Removing ", k, v
            del user_values[k]

    return user_values
 
def submit_ogusa_calculation(mods, first_budget_year):
    print "mods is ", mods
    #user_mods = package_up_vars(mods, first_budget_year)
    user_mods = filter_ogusa_only(mods)
    if not bool(user_mods):
        return False
    print "user_mods is ", user_mods
    print "submit dynamic work"
    user_mods={first_budget_year:user_mods}

    hostnames = DROPQ_WORKERS
    num_hosts = len(hostnames)

    DEFAULT_PARAMS = {
        'callback': "http://localhost:8000/dynamic"  + "/dynamic_finished",
        'params': '{}',
    }

    data = {}
    data['user_mods'] = json.dumps(user_mods)
    job_ids = []
    hostname_idx = 0
    submitted = False
    registered = False
    attempts = 0
    while not submitted:
        theurl = "http://{hn}/example_start_job".format(hn=hostnames[hostname_idx])
        try:
            response = requests.post(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
            if response.status_code == 200:
                print "submitted: ", hostnames[hostname_idx]
                submitted = True
                hostname_idx = (hostname_idx + 1) % num_hosts
                resp_data = json.loads(response.text)
                job_ids.append((resp_data['job_id'], hostnames[hostname_idx]))
            else:
                print "FAILED: ", hostnames[hostname_idx]
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

    params = DEFAULT_PARAMS.copy()
    params['job_id'] = job_ids[0]
    reg_url = "http://" + hostnames[0] + "/register_job"
    register = requests.post(reg_url, data=params)

    while not registered:
        reg_url = "http://{hn}/register_job".format(hn=hostnames[hostname_idx])
        try:
            params = DEFAULT_PARAMS.copy()
            params['job_id'] = job_ids[0][0]
            reg_url = "http://" + hostnames[0] + "/register_job"

            register = requests.post(reg_url, data=params, timeout=TIMEOUT_IN_SECONDS)
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



    return job_ids



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

def ogusa_get_results(job_ids, status):
    '''
    job_ids = celery ID and hostname of job
    status = either "SUCCESS" or "FAILURE"
    '''
    id_hostname  = job_ids[0]
    id_, hostname = id_hostname
    result_url = "http://{hn}/dropq_get_result".format(hn=hostname)
    job_response = requests.get(result_url, params={'job_id':id_})
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
        raise UnknownStatusException(msg)

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


def job_submitted(email_addr, job_id):
    """
    This view sends an email to say that a job was submitted
    """

    url = "http://www.ospc.org/taxbrain/dynamic/{job}".format(job=job_id)

    send_mail(subject="Your TaxBrain simulation has been submitted!",
        message = """Hello!

        Good news! Your TaxBrain simulation has been submitted.
        Your job ID is {job}. We'll notify you again when your job is complete.

        Best,
        The TaxBrain Team""".format(url=url, job=job_id),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    return


def ogusa_results_to_tables(results, first_budget_year):
    """
    Take various results from dropq, i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display
    """
    num_years = 10 
    years = list(range(first_budget_year,
                       first_budget_year + num_years))

    tables = {}
    for table_id in results:

        if table_id == 'df_ogusa':
            row_keys = OGUSA_RESULTS_TOTAL_ROW_KEYS 
            row_labels = OGUSA_RESULTS_TOTAL_ROW_KEY_LABELS 
            add_col1 = "-".join([str(years[0]), str(years[-1])])
            add_col2= "Steady State"
            col_labels = years + [add_col1, add_col2]
            col_formats = [ [1, 'Percent', 3] for y in col_labels]
            table_data = results[table_id]
            multi_year_cells = False

        else:
            raise ValueError("Not a valid key")

        table = {
            'col_labels': col_labels,
            'cols': [],
            'label': OGUSA_RESULTS_TABLE_LABELS[table_id],
            'rows': [],
            'multi_valued': multi_year_cells
        }

        for col_key, label in enumerate(col_labels):
            table['cols'].append({
                'label': label,
                'divisor': col_formats[col_key][0],
                'units': col_formats[col_key][1],
                'decimals': col_formats[col_key][2],
            })

        col_count = len(col_labels)
        for row_key in row_keys:
            row = {
                'label': row_labels[row_key],
                'cells': []
            }

            for col_key in range(0, col_count):
                cell = {
                    'year_values': {},
                    'format': {
                        'divisor': table['cols'][col_key]['divisor'],
                        'decimals': table['cols'][col_key]['decimals'],
                    }
                }

                if multi_year_cells:
                    for yi, year in enumerate(years):
                        value = table_data["{0}_{1}".format(row_key, yi)][col_key]
                        if value[-1] == "%":
                            value = value[:-1]
                        cell['year_values'][year] = value

                    cell['first_value'] = cell['year_values'][first_budget_year]

                else:
                    value = table_data[row_key][col_key]
                    if value[-1] == "%":
                            value = value[:-1]
                    cell['value'] = value

                row['cells'].append(cell)

            table['rows'].append(row)

        tables[table_id] = table


    tables['result_years'] = years
    return tables


def success_text():
    '''
    The text of the email to indicate a successful simulation
    '''
    message = """Hello!

    Good news! Your simulation is done and you can now view the results. Just navigate to
    {url} and have a look!

    Best,
    The TaxBrain Team"""
    return message

def failure_text(traceback):
    '''
    The text of the email to indicate a successful simulation
    traceback: the traceback to include in the email
    '''
    message = """Hello!

    There was a problem with your simulation and your jobs has failed.
    The tracebrack generated by the failed job is:
    {traceback}

    Better luck next time!
    The TaxBrain Team""".format(traceback=traceback)
    return message
