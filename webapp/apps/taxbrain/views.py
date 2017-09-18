from __future__ import print_function
import csv
import pdfkit
import json
import pytz
import os
import tempfile
import re

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['matplotlib', 'matplotlib.pyplot', 'mpl_toolkits',
                'mpl_toolkits.mplot3d']
ENABLE_QUICK_CALC = bool(os.environ.get('ENABLE_QUICK_CALC', ''))
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)


import taxcalc
import datetime
import logging
from urlparse import urlparse, parse_qs
from ipware.ip import get_real_ip

from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import loader, Context
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.models import User
from django import forms

from djqscsv import render_to_csv_response

from .forms import PersonalExemptionForm, has_field_errors
from .models import TaxSaveInputs, OutputUrl, JSONReformTaxCalculator, ErrorMessageTaxCalculator
from .helpers import (default_policy, taxcalc_results_to_tables, format_csv,
                      is_wildcard, convert_val, make_bool, nested_form_parameters,
                      to_json_reform, parse_fields)
from .compute import DropqCompute, MockCompute, JobFailError

dropq_compute = DropqCompute()

from ..constants import (DIAGNOSTIC_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, EXPANDED_TOOLTIP, ADJUSTED_TOOLTIP,
                         FISCAL_CURRENT_LAW, FISCAL_REFORM, FISCAL_CHANGE,
                         INCOME_BINS_TOOLTIP, INCOME_DECILES_TOOLTIP, START_YEAR,
                         START_YEARS)

from ..formatters import get_version

from django.conf import settings
WEBAPP_VERSION = settings.WEBAPP_VERSION

tcversion_info = taxcalc._version.get_versions()

TAXCALC_VERSION = tcversion_info['version']

JOB_PROC_TIME_IN_SECONDS = 30


def log_ip(request):
    """
    Attempt to get the IP address of this request and log it
    """
    ip = get_real_ip(request)
    if ip is not None:
        # we have a real, public ip address for user
        print("BEGIN DROPQ WORK FROM: ", ip)
    else:
        # we don't have a real, public ip address for user
        print("BEGIN DROPQ WORK FROM: unknown IP")


def benefit_switch_fixup(request, reform, model, name="ID_BenefitSurtax_Switch"):
    """
    Take the incoming POST, the user reform, and the TaxSaveInputs
    model and fixup the switches _0, ..., _6 to one array of
    bools. Also set the model values correctly based on incoming
    POST
    """
    _ids = [name + '_' + str(i) for i in range(7)]
    values_from_model = [[reform[_id][0] for _id in _ids]]
    final_values = [[1.0 if _id in request else switch for (switch, _id) in zip(values_from_model[0], _ids)]]
    for _id, val in zip(_ids, final_values[0]):
        reform[_id] = [val]
        setattr(model, _id, unicode(val))
    return reform

def amt_fixup(request, reform, model):
    """
    Take the regular tax captial gains parameters from the user reform
    and set them as the equivalent Alternative Minimum Tax capital
    gains parameters
    """
    cap_gains_params = ["CG_rt1", "CG_brk1_0", "CG_brk1_1",
                        "CG_brk1_2", "CG_brk1_3", "CG_brk1_cpi",
                        "CG_rt2", "CG_brk2_0", "CG_brk2_1",
                        "CG_brk2_2", "CG_brk2_3", "CG_brk2_cpi",
                        "CG_rt3"]

    for cgparam in cap_gains_params:
        if cgparam in reform:
            reform['AMT_' + cgparam] = reform[cgparam]
            if cgparam.endswith("_cpi"):
                setattr(model, 'AMT_' + cgparam, reform[cgparam])
            else:
                setattr(model, 'AMT_' + cgparam, reform[cgparam][0])

    return reform

def growth_fixup(mod):
    if mod['growth_choice']:
        if mod['growth_choice'] == 'factor_adjustment':
            del mod['factor_target']
        if mod['growth_choice'] == 'factor_target':
            del mod['factor_adjustment']
    else:
        if 'factor_adjustment' in mod:
            del mod['factor_adjustment']
        if 'factor_target' in mod:
            del mod['factor_target']

    del mod['growth_choice']

    return mod


def denormalize(x):
    ans = ["#".join([i[0],i[1]]) for i in x]
    ans = [str(x) for x in ans]
    return ans


def normalize(x):
    ans = [i.split('#') for i in x]
    return ans


def parse_errors_warnings(errors_warnings, map_back_to_tb):
    """
    Parse error messages so that they can be mapped to Taxbrain param ID. This
    allows the messages to be displayed under the field where the value is
    entered.

    returns: dictionary 'parsed' with keys: 'errors' and 'warnings'
        parsed['errors/warnings'] = {year: {tb_param_name: 'error message'}}
    """
    parsed = {'errors': {}, 'warnings': {}}
    for action in errors_warnings:
        msgs = errors_warnings[action]
        if len(msgs) == 0:
            continue
        for msg in msgs.split('\n'):
            if len(msg) == 0: # new line
                continue
            msg_spl = msg.split()
            msg_action = msg_spl[0]
            year = msg_spl[1]
            curr_id = msg_spl[2]
            msg_parse = msg_spl[3:]
            if year not in parsed[action]:
                parsed[action][year] = {}
            parsed[action][year][curr_id[1:]] = ' '.join([msg_action] + msg_parse +
                                                         ['for', year])

    return parsed

def read_json_reform(reform, assumptions, map_back_to_tb={}):
    """
    Read reform and parse errors

    returns reform and assumption dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    policy_dict = taxcalc.Calculator.read_json_param_files(
        reform,
        assumptions,
        arrays_not_lists=False
    )
    # get errors and warnings on parameters that do not cause ValueErrors
    errors_warnings = taxcalc.dropq.reform_warnings_errors(policy_dict)
    errors_warnings = parse_errors_warnings(errors_warnings,
                                            map_back_to_tb)
    # separate reform and assumptions
    reform_dict = policy_dict["policy"]
    assumptions_dict = {k: v for k, v in policy_dict.items() if k != "policy"}

    return reform_dict, assumptions_dict, errors_warnings

def get_reform_from_file(request):
    """
    Parse files from request object and collect errors_warnings

    returns reform and assumptions dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            raw reform and assumptions text
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    inmemfile_reform = request.FILES['docfile']
    reform_text = inmemfile_reform.read()
    reform_file = tempfile.NamedTemporaryFile(delete=False)
    reform_file.write(reform_text)
    reform_file.close()
    if 'assumpfile' in request.FILES:
        inmemfile_assumption = request.FILES['assumpfile']
        assumptions_text = inmemfile_assumption.read()
        assumptions_file = tempfile.NamedTemporaryFile(delete=False)
        assumptions_file.write(assumptions_text)
        assumptions_file.close()
        assumptions_file_name = assumptions_file.name
    else:
        assumptions_text = ""
        assumptions_file_name = None

    (reform_dict, assumptions_dict,
        errors_warnings) = read_json_reform(reform_file.name,
                                            assumptions_file_name)

    return (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings)


def get_reform_from_gui(request, taxbrain_model=None, behavior_model=None,
                        stored_errors=None):
    """
    Parse request and model objects and collect reforms and warnings
    This function is also called by dynamic/views.behavior_model.  In the
    future, this could be used as a generic GUI parameter parsing function.

    returns reform and assumptions dictionaries that are compatible with
            taxcalc.Policy.implement_reform
            raw reform and assumptions text
            parsed warning and error messsages to be displayed on input page
            if necessary
    """
    start_year = request.REQUEST['start_year']
    taxbrain_data = {}
    assumptions_data = {}
    map_back_to_tb = {}

    policy_dict_json = {}
    assumptions_dict_json = {}

    # prepare taxcalc params from TaxSaveInputs model
    if taxbrain_model is not None:
        taxbrain_data = dict(taxbrain_model.__dict__)
        taxbrain_data = growth_fixup(taxbrain_data)
        taxbrain_data = parse_fields(taxbrain_data)
        taxbrain_data = benefit_switch_fixup(request.REQUEST,
                                             taxbrain_data,
                                             taxbrain_model,
                                             name="ID_BenefitSurtax_Switch")
        taxbrain_data = benefit_switch_fixup(request.REQUEST,
                                             taxbrain_data,
                                             taxbrain_model,
                                             name="ID_BenefitCap_Switch")
        taxbrain_data = amt_fixup(request.REQUEST,
                                  taxbrain_data,
                                  taxbrain_model)
        # convert GUI input to json style taxcalc reform
        policy_dict_json, map_back_to_tb = to_json_reform(taxbrain_data,
                                                          int(start_year))
    if behavior_model is not None:
        assumptions_data = dict(behavior_model.__dict__)
        assumptions_data = parse_fields(assumptions_data)
        (assumptions_dict_json,
            map_back_assump) = to_json_reform(assumptions_data,
                                              int(start_year),
                                              cls=taxcalc.Behavior)
        map_back_to_tb.update(map_back_assump)

    policy_dict_json = {"policy": policy_dict_json}

    policy_dict_json = json.dumps(policy_dict_json)

    assumptions_dict_json = {"behavior": assumptions_dict_json,
                             "growdiff_response": {},
                             "consumption": {},
                             "growdiff_baseline": {}}
    assumptions_dict_json = json.dumps(assumptions_dict_json)

    (reform_dict, assumptions_dict,
        errors_warnings) = read_json_reform(policy_dict_json,
                                            assumptions_dict_json,
                                            map_back_to_tb)

    return (reform_dict, assumptions_dict, "", "", errors_warnings)


def submit_reform(request, user=None):
    """
    Submits TaxBrain reforms.  This handles data from the GUI interface
    and the file input interface.  With some tweaks this model could be used
    to submit reforms for all PolicyBrain models

    returns OutputUrl object with parsed user input and warning/error messages
            if necessary
            boolean variable indicating whether this reform has errors or not

    """
    start_year = START_YEAR
    no_inputs = False

    has_errors = make_bool(request.POST['has_errors'])
    taxcalc_errors = False
    taxcalc_warnings = False
    is_valid = True
    has_parse_errors = False
    start_year = request.REQUEST['start_year']
    fields = dict(request.REQUEST)
    #TODO: use either first_year or start_year; validation error is thrown
    # if start_year not in fields
    fields['first_year'] = fields['start_year']
    # Assume we do the full calculation unless we find out otherwise
    do_full_calc = False if fields.get('quick_calc') else True
    if do_full_calc and 'full_calc' in fields:
        del fields['full_calc']
    elif 'quick_calc' in fields:
        del fields['quick_calc']
    errors_warnings = {'warnings': {}, 'errors': {}}
    reform_dict = {}
    personal_inputs = None
    is_file = False
    if 'docfile' in request.FILES:
        is_file = True
        model = None
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = get_reform_from_file(request)
    else:
        personal_inputs = PersonalExemptionForm(start_year, fields)
        # If an attempt is made to post data we don't accept
        # raise a 400
        if personal_inputs.non_field_errors():
            return HttpResponse("Bad Input!", status=400), True
        is_valid = personal_inputs.is_valid()
        if is_valid:
            model = personal_inputs.save()
            (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings) = get_reform_from_gui(request,
                                                       taxbrain_model=model)

    if reform_dict == {}:
        no_inputs = True
    # TODO: account for errors
    # first only account for GUI errors
    # 5 cases:
    #   0. no warning/error messages --> run model
    #   1. has seen warning/error messages and now there are no errors -- > run model
    #   2. has not seen warning/error messages --> show warning/error messages
    #   3. has seen warning/error messages and there are still error messages
    #        --> show warning/error messages again
    #   4. no user input --> do not run model

    warn_msgs = errors_warnings['warnings'] != {}
    stop_errors = no_inputs or not is_valid or errors_warnings['errors'] != {}

    if stop_errors or (not has_errors and warn_msgs):
        taxcalc_errors = True if errors_warnings['errors'] else False
        taxcalc_warnings = True if errors_warnings['warnings'] else False
        if personal_inputs is not None:
            # TODO: parse warnings for file_input
            # only handle GUI errors for now
            if ((taxcalc_errors or taxcalc_warnings)
                    and personal_inputs is not None):
                for action in errors_warnings:
                    for year in sorted(errors_warnings[action].keys(),
                                       key=lambda x: float(x)):
                        for param in errors_warnings[action][year]:
                            personal_inputs.add_error(
                                param,
                                errors_warnings[action][year][param]
                            )
            has_parse_errors = any(['Unrecognize value' in e[0]
                                    for e in personal_inputs.errors.values()])
            if no_inputs:
                personal_inputs.add_error(
                    None,
                    "Please specify a tax-law change before submitting."
                )
            if taxcalc_warnings or taxcalc_errors:
                msg = ("Some fields have errors. Values outside of suggested "
                       "ranges will be accepted if they only cause warnings "
                       "and are submitted again from this page.")
                personal_inputs.add_error(None, msg)
            if has_parse_errors:
                msg = ("Some fields have unrecognized values. Enter comma "
                       "separated values for each input.")
                personal_inputs.add_error(None, msg)

        return (personal_inputs, any([taxcalc_errors, taxcalc_warnings,
                no_inputs, not is_valid]))
    # case where user has been warned and has fixed errors if necassary but may
    # or may not have fixed warnings
    if has_errors:
        assert not taxcalc_errors
    # try: # TODO: is try-catch necessary here?
    log_ip(request)
    # TODO: drop is_file and package_up_user_mods keywords
    if do_full_calc:
        submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(
            reform_dict,
            int(start_year),
            is_file=is_file,
            additional_data=assumptions_dict,
            package_up_user_mods=False
        )
    else:
        submitted_ids, max_q_length = dropq_compute.submit_dropq_small_calculation(
            reform_dict,
            int(start_year),
            is_file=is_file,
            additional_data=assumptions_dict,
            package_up_user_mods=False
        )
    job_ids = denormalize(submitted_ids)
    json_reform = JSONReformTaxCalculator()
    # save file_input user params
    if is_file:
        json_reform.reform_text = json.dumps(reform_dict)
        json_reform.assumption_text = json.dumps(assumptions_dict)
        json_reform.raw_reform_text = reform_text
        json_reform.raw_assumption_text = assumptions_text
    # save GUI user params
    else:
        job_ids = denormalize(submitted_ids)
        model.job_ids = job_ids
        model.first_year = int(start_year)
        model.quick_calc = not do_full_calc
        model.save()
        unique_url = OutputUrl()

        json_reform.reform_text = json.dumps(reform_dict)
        json_reform.assumption_text = json.dumps(assumptions_dict)
        json_reform.raw_reform_text = ""
        json_reform.raw_assumption_text = ""

    json_reform.save()

    # create model for file_input case
    if model is None:
        model = TaxSaveInputs()
    model.job_ids = job_ids
    model.json_text = json_reform
    model.first_year = int(start_year)
    model.quick_calc = not do_full_calc
    model.save()

    # create OutputUrl object
    unique_url = OutputUrl()
    if user:
        unique_url.user = user
    elif request and request.user.is_authenticated():
        current_user = User.objects.get(pk=request.user.id)
        unique_url.user = current_user

    if unique_url.taxcalc_vers is not None:
        pass
    else:
        unique_url.taxcalc_vers = TAXCALC_VERSION
    if unique_url.webapp_vers != None:
        pass
    else:
        unique_url.webapp_vers = WEBAPP_VERSION

    unique_url.unique_inputs = model
    unique_url.model_pk = model.pk
    cur_dt = datetime.datetime.utcnow()
    future_offset_seconds = ((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS)
    future_offset = datetime.timedelta(seconds=future_offset_seconds)
    expected_completion = cur_dt + future_offset
    unique_url.exp_comp_datetime = expected_completion
    unique_url.save()
    return (unique_url, any([taxcalc_errors, taxcalc_warnings, no_inputs,
            not is_valid]))


def file_input(request):
    """
    Receive request from file input interface and returns parsed data or an
    input form
    """
    start_year = START_YEAR
    errors = None

    if request.method=='POST':
        # File is not submitted
        if 'docfile' not in dict(request.FILES):
            errors = ["Please specify a tax-law change before submitting."]
        else:
            unique_url, has_errors = submit_reform(request)
            # TODO: handle taxcalc_errors and taxcalc_warnings
            return redirect(unique_url)
    # GET request, load a default form
    params = parse_qs(urlparse(request.build_absolute_uri()).query)
    if 'start_year' in params and params['start_year'][0] in START_YEARS:
        start_year = params['start_year'][0]

    init_context = {
        'form': None,
        'errors': errors,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'params': None, # TODO: doesn't do anything-->: taxcalc_default_params,
        'start_years': START_YEARS,
        'start_year': start_year,
        'enable_quick_calc': ENABLE_QUICK_CALC
    }

    return render(request, 'taxbrain/input_file.html', init_context)


def personal_results(request):
    """
    Receive data from GUI interface and returns parsed data or default data if
    get request
    """
    start_year = START_YEAR
    has_errors = False
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        start_year = request.REQUEST['start_year']
        fields = dict(request.REQUEST)
        # TODO: find better solution for full_calc vs quick_calc
        # Assume we do the full calculation unless we find out otherwise
        do_full_calc = False if fields.get('quick_calc') else True
        fields['first_year'] = fields['start_year']
        if do_full_calc and 'full_calc' in fields:
            del fields['full_calc']
        elif 'quick_calc' in fields:
            del fields['quick_calc']

        obj, has_errors = submit_reform(request)

        # case where validation failed in forms.PersonalExemptionForm
        # TODO: assert HttpResponse status is 404
        if has_errors and isinstance(obj, HttpResponse):
            return obj

        # No errors--submit to model
        if not has_errors:
            return redirect(obj)
        # Errors from taxcalc.dropq.reform_warnings_errors
        else:
            personal_inputs = obj

    else:
        # Probably a GET request, load a default form
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        personal_inputs = PersonalExemptionForm(first_year=start_year)


    init_context = {
        'form': personal_inputs,
        'params': nested_form_parameters(int(start_year)),
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'enable_quick_calc': ENABLE_QUICK_CALC
    }

    return render(request, 'taxbrain/input_form.html', init_context)


def submit_micro(request, pk):
    """
    This view handles the re-submission of a previously submitted microsim.
    Its primary purpose is to facilitate a mechanism to submit a full microsim
    job after one has submitted parameters for a 'quick calculation'
    """
    #TODO: get this function to work with submit_reform
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = TaxSaveInputs.objects.get(pk=url.model_pk)
    # This will be a new model instance so unset the primary key
    model.pk = None
    # Unset the computed results, set quick_calc to False
    # (this new model instance will be saved in process_model)
    model.job_ids = None
    model.jobs_not_ready = None
    model.quick_calc = False
    model.tax_result = None

    log_ip(request)
    unique_url = process_model(model, start_year=str(model.first_year),
                               do_full_calc=True, user=url.user)
    return redirect(unique_url)


def edit_personal_results(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = TaxSaveInputs.objects.get(pk=url.model_pk)
    start_year = model.first_year

    form_personal_exemp = PersonalExemptionForm(first_year=start_year, instance=model)

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': nested_form_parameters(int(start_year)),
        'taxcalc_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_years': START_YEARS,
        'start_year': str(start_year),
        'is_edit_page': True
    }

    return render(request, 'taxbrain/input_form.html', init_context)


def add_summary_column(table):
    import copy
    summary = copy.deepcopy(table["cols"][-1])
    summary["label"] = "Total"
    table["cols"].append(summary)
    table["col_labels"].append("Total")
    for x in table["rows"]:
        row_total = 0
        for y in x["cells"]:
            row_total += float(y["value"])
        x["cells"].append({
            'format': {
                u'decimals': 1,
                u'divisor': 1000000000
            },
            u'value': unicode(row_total),
            u'year_values': {}
        })
    return table



def get_result_context(model, request, url):
    output = model.tax_result
    first_year = model.first_year
    quick_calc = model.quick_calc
    created_on = model.creation_date
    if model.reform_style:
        rs = [True if x=='True' else False for x in model.reform_style.split(',')]
        allow_dyn_links = True if (len(rs) < 2 or rs[1] is False) else False
    else:
        allow_dyn_links = True
    if 'fiscal_tots' in output:
        # Use new key/value pairs for old data
        output['fiscal_tot_diffs'] = output['fiscal_tots']
        output['fiscal_tot_base'] = output['fiscal_tots']
        output['fiscal_tot_ref'] = output['fiscal_tots']
        del output['fiscal_tots']

    tables = taxcalc_results_to_tables(output, first_year)
    tables["tooltips"] = {
        'diagnostic': DIAGNOSTIC_TOOLTIP,
        'difference': DIFFERENCE_TOOLTIP,
        'payroll': PAYROLL_TOOLTIP,
        'income': INCOME_TOOLTIP,
        'base': BASE_TOOLTIP,
        'reform': REFORM_TOOLTIP,
        'expanded': EXPANDED_TOOLTIP,
        'adjusted': ADJUSTED_TOOLTIP,
        'bins': INCOME_BINS_TOOLTIP,
        'deciles': INCOME_DECILES_TOOLTIP,
        'fiscal_current_law': FISCAL_CURRENT_LAW,
        'fiscal_reform': FISCAL_REFORM,
        'fiscal_change': FISCAL_CHANGE,
    }

    if (model.json_text is not None and (model.json_text.raw_reform_text and
       model.json_text.raw_assumption_text)):
        reform_file_contents = model.json_text.reform_text
        reform_file_contents = reform_file_contents.replace(" ","&nbsp;")
        assump_file_contents = model.json_text.assumption_text
        assump_file_contents = assump_file_contents.replace(" ","&nbsp;")
    else:
        reform_file_contents = False
        assump_file_contents = False

    if hasattr(request, 'user'):
        is_registered = True if request.user.is_authenticated() else False
    else:
        is_registered = False
    tables['fiscal_change'] = add_summary_column(tables['fiscal_tot_diffs'])
    tables['fiscal_currentlaw'] = add_summary_column(tables['fiscal_tot_base'])
    tables['fiscal_reform'] = add_summary_column(tables['fiscal_tot_ref'])
    json_table = json.dumps(tables)

    context = {
        'locals':locals(),
        'unique_url':url,
        'tables': json_table,
        'created_on': created_on,
        'first_year': first_year,
        'quick_calc': quick_calc,
        'is_registered': is_registered,
        'is_micro': True,
        'reform_file_contents': reform_file_contents,
        'assump_file_contents': assump_file_contents,
        'allow_dyn_links': allow_dyn_links,
        'results_type': "static"
    }
    return context


def output_detail(request, pk):
    """
    This view is the single page of diplaying a progress bar for how
    close the job is to finishing, and then it will also display the
    job results if the job is done. Finally, it will render a 'job failed'
    page if the job has failed.
    """

    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = url.unique_inputs

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'taxcalc_version': taxcalc_vers_disp,
                         'webapp_version': webapp_vers_disp}
    if model.tax_result:
        context = get_result_context(model, request, url)
        context.update(context_vers_disp)
        context["raw_reform_text"] = model.json_text.raw_reform_text if model.json_text else ""
        context["raw_assumption_text"] = model.json_text.raw_assumption_text if model.json_text else ""
        return render(request, 'taxbrain/results.html', context)
    elif model.error_text:
        return render(request, 'taxbrain/failed.html', {"error_msg": model.error_text.text})
    else:

        job_ids = model.job_ids
        jobs_to_check = model.jobs_not_ready
        if not jobs_to_check:
            jobs_to_check = normalize(job_ids)
        else:
            jobs_to_check = normalize(jobs_to_check)

        try:
            jobs_ready = dropq_compute.dropq_results_ready(jobs_to_check)
        except JobFailError as jfe:
            print(jfe)
            return render_to_response('taxbrain/failed.html')

        if any([j == 'FAIL' for j in jobs_ready]):
            failed_jobs = [sub_id for (sub_id, job_ready) in
                           zip(jobs_to_check, jobs_ready) if job_ready == 'FAIL']

            #Just need the error message from one failed job
            error_msgs = dropq_compute.dropq_get_results([failed_jobs[0]], job_failure=True)
            error_msg = error_msgs[0]
            val_err_idx = error_msg.rfind("Error")
            error = ErrorMessageTaxCalculator()
            error_contents = error_msg[val_err_idx:].replace(" ","&nbsp;")
            error.text = error_contents
            error.save()
            model.error_text = error
            model.save()
            return render(request, 'taxbrain/failed.html', {"error_msg": error_contents})


        if all([j == 'YES' for j in jobs_ready]):
            results, reform_style = dropq_compute.dropq_get_results(normalize(job_ids))
            model.tax_result = results
            if reform_style:
                rs = ','.join([str(flag) for flag in reform_style])
            else:
                rs = ''
            model.reform_style = rs
            model.creation_date = datetime.datetime.now()
            model.save()
            context = get_result_context(model, request, url)
            context.update(context_vers_disp)
            return render(request, 'taxbrain/results.html', context)

        else:
            jobs_not_ready = [sub_id for (sub_id, job_ready) in
                                zip(jobs_to_check, jobs_ready) if job_ready == 'NO']
            jobs_not_ready = denormalize(jobs_not_ready)
            model.jobs_not_ready = jobs_not_ready
            model.save()
            if request.method == 'POST':
                # if not ready yet, insert number of minutes remaining
                exp_comp_dt = url.exp_comp_datetime
                utc_now = datetime.datetime.utcnow()
                utc_now = utc_now.replace(tzinfo=pytz.utc)
                dt = exp_comp_dt - utc_now
                exp_num_minutes = dt.total_seconds() / 60.
                exp_num_minutes = round(exp_num_minutes, 2)
                exp_num_minutes = exp_num_minutes if exp_num_minutes > 0 else 0
                if exp_num_minutes > 0:
                    return JsonResponse({'eta': exp_num_minutes}, status=202)
                else:
                    return JsonResponse({'eta': exp_num_minutes}, status=200)

            else:
                context = {'eta': '100'}
                context.update(context_vers_disp)
                return render_to_response('taxbrain/not_ready.html', context, context_instance=RequestContext(request))


@permission_required('taxbrain.view_inputs')
def csv_output(request, pk):
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    now = datetime.datetime.now()
    suffix = "".join(map(str, [now.year, now.month, now.day, now.hour, now.minute,
                       now.second]))
    filename = "taxbrain_outputs_" + suffix + ".csv"
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

    results = url.unique_inputs.tax_result
    first_year = url.unique_inputs.first_year
    csv_results = format_csv(results, pk, first_year)
    writer = csv.writer(response)
    for csv_row in csv_results:
        writer.writerow(csv_row)

    return response

@permission_required('taxbrain.view_inputs')
def csv_input(request, pk):
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404


    def filter_names(x):
        """
        Any of these field names we don't care about
        """
        return x not in ['outputurl', 'id', 'inflation', 'inflation_years',
                         'medical_inflation', 'medical_years', 'tax_result',
                         'creation_date']

    field_names = [f.name for f in TaxSaveInputs._meta.get_fields(include_parents=False)]
    field_names = tuple(filter(filter_names, field_names))

    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type='text/csv')
    now = datetime.datetime.now()
    suffix = "".join(map(str, [now.year, now.month, now.day, now.hour, now.minute,
                       now.second]))
    filename = "taxbrain_inputs_" + suffix + ".csv"
    response['Content-Disposition'] = 'attachment; filename="' + filename + '"'

    inputs = url.unique_inputs

    writer = csv.writer(response)
    writer.writerow(field_names)
    writer.writerow([getattr(inputs, field) for field in field_names])

    return response

@permission_required('taxbrain.view_inputs')
def pdf_view(request):
    """
    This view creates the pdfs.
    """
    pdf = pdfkit.from_url(request.META['HTTP_REFERER'], False)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="tax_results.pdf"'

    return response
