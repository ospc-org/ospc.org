import os
import requests
import dropq
import json
import sys
from django.core import serializers

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['numba', 'numba.jit', 'numba.vectorize', 'numba.guvectorize']
                
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

from ..taxbrain.helpers import TaxCalcParam, package_up_vars, default_taxcalc_data
from ..taxbrain.compute import ELASTIC_RESULTS_TOTAL_ROW_KEYS 
from django.core.mail import send_mail
import requests
from requests.exceptions import Timeout, RequestException
ogusa_workers = os.environ.get('OGUSA_WORKERS', '')
OGUSA_WORKERS = ogusa_workers.split(",")
dropq_workers = os.environ.get('DROPQ_WORKERS', '')
DROPQ_WORKERS = dropq_workers.split(",")
OGUSA_WORKER_IDX = 0
CALLBACK_HOSTNAME = os.environ.get('CALLBACK_HOSTNAME', 'localhost:8000')
ENFORCE_REMOTE_VERSION_CHECK = os.environ.get('ENFORCE_VERSION', 'False') == 'True'

OGUSA_RESULTS_TOTAL_ROW_KEYS = dropq.dropq.ogusa_row_names
OGUSA_RESULTS_TOTAL_ROW_KEY_LABELS = {n:n for n in OGUSA_RESULTS_TOTAL_ROW_KEYS}

ELASTIC_RESULTS_TOTAL_ROW_KEY_LABELS = {n:'% Difference in GDP' for n in ELASTIC_RESULTS_TOTAL_ROW_KEYS}
ELASTIC_RESULTS_TABLE_LABELS = {
        'elasticity_gdp': 'Elasticity of GDP wrt 1 - Average Marginal Tax Rate'
        }

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


def strip_empty_lists(l):
    for k, v in l.items():
        l[k] = v[0] if v == [u''] else v


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


def denormalize(x):
    ans = ["#".join([i[0],i[1]]) for i in x]
    ans = [str(x) for x in ans]
    return ans


def normalize(x):
    ans = [i.split('#') for i in x]
    return ans


def increment_ogusa_worker():
    global OGUSA_WORKER_IDX
    OGUSA_WORKER_IDX = (OGUSA_WORKER_IDX + 1) % len(OGUSA_WORKERS)

#
# Prepare user params to send to DropQ/Taxcalc
#

import taxcalc
tcversion_info = taxcalc._version.get_versions()
#ogversion_info = {u'full-revisionid': u'9ae018afc6c80b10fc19684d7ba9aa1729aa2f47',
                  #u'dirty': False, u'version': u'0.1.1', u'error': None}

version_path = os.path.join(os.path.split(__file__)[0], "ogusa_version.json")
with open(version_path, "r") as f:
    ogversion_info = json.load(f)
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


def default_behavior_parameters(first_budget_year):
    ''' Create a list of default Behavior parameters '''
    default_behavior_params = {}
    BEHAVIOR_DEFAULT_PARAMS_JSON = default_taxcalc_data(taxcalc.Behavior,
                                                        metadata=True,
                                                        start_year=first_budget_year)

    for k,v in BEHAVIOR_DEFAULT_PARAMS_JSON.iteritems():
        param = TaxCalcParam(k,v, first_budget_year)
        default_behavior_params[param.nice_id] = param

    return default_behavior_params


def default_elasticity_parameters(first_budget_year):
    ''' Create a list of default Elasticity parameters '''
    default_elasticity_params = {}
    default_value = 0.0
    adj_long_name = ("Elasticity of GDP with respect to 1 - average marginal "
                     "tax rate.")
    adj_descr = ("This parameter describes how many percent GDP will change "
                 "for each 1 percent change in 1 - the average "
                 "marginal tax rate, weighted by wage income, in the "
                 "preceeding year.")

    elasticity_of_gdp = {'value':[default_value], 'col_label':"",
                         'long_name': adj_long_name,
                         'description': adj_descr,
                         'irs_ref':'', 'notes':''}

    ELASTICITY_DEFAULT_PARAMS_JSON = {'elastic_gdp': elasticity_of_gdp}

    for k,v in ELASTICITY_DEFAULT_PARAMS_JSON.iteritems():
        param = TaxCalcParam(k,v, first_budget_year)
        default_elasticity_params[param.nice_id] = param

    return default_elasticity_params


def default_parameters(first_budget_year):
    ''' Create a list of default parameters '''

    param_path = os.path.join(os.path.split(__file__)[0], "ogusa_parameters.json")
    with open(param_path, "r") as f:
        OGUSA_DEFAULT_PARAMS_JSON = json.load(f)

    default_ogusa_params = {}
    for k,v in OGUSA_DEFAULT_PARAMS_JSON.iteritems():
        #TaxCalcParams expect list
        if 'value' in v:
            v['value'] = [v['value']]
        param = TaxCalcParam(k,v, first_budget_year)
        default_ogusa_params[param.nice_id] = param

    return default_ogusa_params


def filter_ogusa_only(user_values):

    unused_names = ['first_year', 'creation_date', '_state', 'id', 'user_email']

    for k, v in user_values.items():
        if k in unused_names:
            print "Removing ", k, v
            del user_values[k]
        else:
            user_values[k] = float(v)

    return user_values
 
def submit_ogusa_calculation(mods, first_budget_year, microsim_data):
    print "mods is ", mods
    ogusa_mods = filter_ogusa_only(mods)
    microsim_params = package_up_vars(microsim_data, first_budget_year)
    print "submit dynamic work"
    print "ogusa_mods is ", ogusa_mods

    hostnames = OGUSA_WORKERS

    DEFAULT_PARAMS = {
        'callback': "http://{}/dynamic/dynamic_finished".format(CALLBACK_HOSTNAME),
    }

    data = {}
    data['ogusa_params'] = json.dumps(ogusa_mods)
    microsim_mods = {first_budget_year:microsim_params}
    data['user_mods'] = json.dumps(microsim_mods)
    job_ids = []
    guids = []
    hostname_idx = OGUSA_WORKER_IDX
    submitted = False
    registered = False
    attempts = 0
    while not submitted:
        theurl = "http://{hn}/ogusa_start_job".format(hn=hostnames[hostname_idx])
        try:
            response = requests.post(theurl, data=data, timeout=TIMEOUT_IN_SECONDS)
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
            increment_ogusa_worker()
            attempts += 1
        except RequestException as re:
            print "Something unexpected happened: ", re
            increment_ogusa_worker()
            attempts += 1
        if attempts > MAX_ATTEMPTS_SUBMIT_JOB:
            print "Exceeded max attempts. Bailing out."
            increment_ogusa_worker()
            raise IOError()

    params = DEFAULT_PARAMS.copy()
    params['job_id'] = job_ids[0]
    reg_url = "http://" + hostnames[hostname_idx] + "/register_job"
    register = requests.post(reg_url, data=params)

    while not registered:
        reg_url = "http://{hn}/register_job".format(hn=hostnames[hostname_idx])
        try:
            params = DEFAULT_PARAMS.copy()
            params['job_id'] = job_ids[0][0]
            reg_url = "http://" + hostnames[hostname_idx] + "/register_job"

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

    # We increment upon exceptions to submit, but once we have submitted and
    # registered, increment again to move to the next OGUSA worker node
    increment_ogusa_worker()
    return job_ids, guids


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


def job_submitted(email_addr, model):
    """
    Send emails to say that a job was submitted
    """

    job_ids = model.job_ids
    url = "http://www.ospc.org/taxbrain/dynamic/{job}".format(job=job_ids)
    submitted_ids_and_ips = normalize(job_ids)
    submitted_id, submitted_ip = submitted_ids_and_ips[0]
    send_mail(subject="Your TaxBrain simulation has been submitted!",
        message = """Hello!

        Good news! Your TaxBrain simulation has been submitted.
        Your job ID is {job}. We'll notify you again when your job is complete.

        Best,
        The TaxBrain Team""".format(url=url, job=submitted_id),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    email_txt, subj_txt = cc_text_submitted()
    send_cc_email(email_txt, subj_txt, model)
    return


def dynamic_params_from_model(model):
    '''Get user-submitted dynamic parameters from a DynamicSaveInputs model'''
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)
    inputs = user_inputs[0]['fields']

    # Read user-modifiable parameters list from file
    usermods_path = os.path.join(os.path.split(__file__)[0],
                                 "ogusa_user_modifiable.json")
    with open(usermods_path, "r") as f:
         ump = json.load(f)
         USER_MODIFIABLE_PARAMS = ump["USER_MODIFIABLE_PARAMS"]
    params = {k:inputs[k] for k in USER_MODIFIABLE_PARAMS}
    return params


def send_cc_email(email_txt, subject_txt, model):
    ''' Send email_txt in a CC email to the users on the
        CC_EMAIL_ADDRESSES list
    '''

    pk = model.micro_sim.pk
    job_ids = model.job_ids
    submitted_ids = normalize(job_ids)
    #Get the celery ID and IP address of the job
    job_id, ip_addr = submitted_ids[0]

    #Get the globally unique ID of the job
    guids = model.guids
    guids = normalize(guids)
    _, guid = guids[0]

    #Get the user-input from the model in a way we can render
    params = dynamic_params_from_model(model)

    #Create the path information for debugging info to include in the email
    baseline = "/home/ubuntu/dropQ/OUTPUT_BASELINE_{guid}".format(guid=guid)
    policy = "/home/ubuntu/dropQ/OUTPUT_REFORM_{guid}".format(guid=guid)
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    microsim_url = hostname + "/taxbrain/" + str(pk)
    cc_txt = email_txt.format(microsim_url=microsim_url,
                              job_id=job_id, params=params,
                              hostname=ip_addr, baseline=baseline,
                              policy=policy)

    other_email_addrs = os.environ.get('CC_EMAIL_ADDRESSES', None)
    if other_email_addrs:
        other_email_addrs = other_email_addrs.split(',')
        send_mail(subject=subject_txt,
                  message=cc_txt,
                  from_email="Open Source Policy Center <mailing@ospc.org>",
                  recipient_list=other_email_addrs)

    return


def elast_results_to_tables(results, first_budget_year):
    """
    Take various results from elastiticty calculation, 
    Return organized and labeled table results for display
    """
    num_years = NUM_BUDGET_YEARS
    years = list(range(first_budget_year,
                       first_budget_year + num_years))

    def format_float_values(x):
        try:
            return 100. * float(x)
        except ValueError:
            return x

    tables = {}

    for table_id in results:

        if table_id == 'elasticity_gdp':
            row_keys = ELASTIC_RESULTS_TOTAL_ROW_KEYS 
            row_labels = ELASTIC_RESULTS_TOTAL_ROW_KEY_LABELS 
            col_labels = years
            col_formats = [ [1, '%', 1] for y in col_labels]

            table_data = results[table_id]
            #Displaying as a percentage, so multiply by 100
            for k, v in table_data.iteritems():
                table_data[k] = list(map(str, map(format_float_values, v)))
            multi_year_cells = False

        else:
            raise ValueError("Not a valid key")

        table = {
            'col_labels': col_labels,
            'cols': [],
            'label': ELASTIC_RESULTS_TABLE_LABELS[table_id],
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



def ogusa_results_to_tables(results, first_budget_year):
    """
    Take various results from dropq, i.e. mY_dec, mX_bin, df_dec, etc
    Return organized and labeled table results for display
    """
    num_years = NUM_BUDGET_YEARS
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
            col_formats = [ [1, '%', 2] for y in col_labels]

            table_data = results[table_id]
            #Displaying as a percentage, so multiply by 100
            for k, v in table_data.iteritems():
                table_data[k] = list(map(str, map(lambda x: 100.*x, map(float, v))))
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

    This dynamic simulation has job ID {job_id} was based on the microsimulation
    results found here:

    {microsim_url}

    You used the following macroeconomic model parameters: {params}

    Best,
    The TaxBrain Team"""
    return message

def failure_text():
    '''
    The text of the email to indicate a successful simulation
    traceback: the traceback to include in the email
    '''
    message = """Hello!

    There was a problem with your simulation and your jobs has failed.
    The tracebrack generated by the failed job is:
    {traceback}

    This dynamic simulation has job ID {job_id} was based on the microsimulation
    results found here:

    {microsim_url}

    You used the following macroeconomic model parameters: {params}

    Better luck next time!
    The TaxBrain Team"""
    return message


def cc_text_base():
    '''
    The base text of the email to send to the CC list when a simulation
    starts or completes
    '''
    message = """This dynamic simulation has job ID {job_id} and was based on the
    microsimulation results found here:

    {microsim_url}

    They used the following macroeconomic model parameters: {params}

    The hostname for the node that computed the result is: {hostname}

    The path for the baseline run is: {baseline}

    The path for the policy run is: {policy}

    Best,
    The TaxBrain Team"""
    return message


def cc_text_finished(url):
    '''
    The text of the email to send to the CC list when a simulation completes
    '''
    message = """Hello!

    Someone has just finished a dynamic scoring simulation! Just navigate to
    {url} and have a look! """

    message = message.format(url=url)
    message += cc_text_base()
    subject_text = "A TaxBrain simulation has completed!"

    return message, subject_text


def cc_text_submitted():
    '''
    The text of the email to send to the CC list when a simulation is
    submitted.
    '''
    message = """Hello!

    Someone has just submitted a dynamic scoring simulation!
    """

    message += cc_text_base()
    subject_text = "A TaxBrain simulation has been submitted!"

    return message, subject_text


def cc_text_failure(traceback):
    '''
    The text of the email to send to the CC list when a simulation fails
    '''
    message = """Hello!

    Someone has just had a failure in running a dynamic scoring simulation. 
    The tracebrack generated by the failed job is:

    """
    message += traceback
    message += cc_text_base()
    subject_text = "A TaxBrain simulation has completed!"

    return message, subject_text
