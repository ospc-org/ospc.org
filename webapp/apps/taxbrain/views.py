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
from django.template.context_processors import csrf
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

from .forms import TaxBrainForm, has_field_errors
from .models import TaxSaveInputs, OutputUrl, JSONReformTaxCalculator, ErrorMessageTaxCalculator
from .helpers import (default_policy, taxcalc_results_to_tables, format_csv,
                      is_wildcard, convert_val, make_bool, nested_form_parameters,
                      )
from .compute import (DropqCompute, MockCompute, JobFailError, NUM_BUDGET_YEARS,
                      NUM_BUDGET_YEARS_QUICK)

dropq_compute = DropqCompute()

from ..constants import (DISTRIBUTION_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, FISCAL_CURRENT_LAW, FISCAL_REFORM,
                         FISCAL_CHANGE, INCOME_BINS_TOOLTIP,
                         INCOME_DECILES_TOOLTIP, START_YEAR, START_YEARS)

from ..formatters import get_version
from .param_formatters import (get_reform_from_file, get_reform_from_gui,
                               to_json_reform)

from django.conf import settings
WEBAPP_VERSION = settings.WEBAPP_VERSION

tcversion_info = taxcalc._version.get_versions()

TAXCALC_VERSION = tcversion_info['version']

JOB_PROC_TIME_IN_SECONDS = 30

OUT_OF_RANGE_ERROR_MSG = ("Some fields have warnings or errors. Values "
                          "outside of suggested ranges will be accepted if "
                          "they only cause warnings and are submitted again "
                          "from this page. Warning messages begin with "
                          "'WARNING', and error messages begin with 'ERROR'.")

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

def denormalize(x):
    ans = ["#".join([i[0],i[1]]) for i in x]
    ans = [str(x) for x in ans]
    return ans


def normalize(x):
    ans = [i.split('#') for i in x]
    return ans

def save_model(url, request, model, json_reform, has_errors, start_year,
               do_full_calc, is_file, reform_dict, assumptions_dict,
               reform_text, assumptions_text, submitted_ids,
               max_q_length, user):
    """
    Save user input data
    returns OutputUrl object
    """
    # create model for file_input case
    if model is None:
        model = TaxSaveInputs()
    model.job_ids = denormalize(submitted_ids)
    model.json_text = json_reform
    model.first_year = int(start_year)
    model.quick_calc = not do_full_calc
    model.save()

    # create OutputUrl object
    if url is None:
        unique_url = OutputUrl()
    else:
        unique_url = url
    if user:
        unique_url.user = user
    elif request and request.user.is_authenticated():
        current_user = User.objects.get(pk=request.user.id)
        unique_url.user = current_user

    if unique_url.taxcalc_vers is None:
        unique_url.taxcalc_vers = TAXCALC_VERSION
    if unique_url.webapp_vers is None:
        unique_url.webapp_vers = WEBAPP_VERSION

    unique_url.unique_inputs = model
    unique_url.model_pk = model.pk
    cur_dt = datetime.datetime.utcnow()
    future_offset_seconds = ((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS)
    future_offset = datetime.timedelta(seconds=future_offset_seconds)
    expected_completion = cur_dt + future_offset
    unique_url.exp_comp_datetime = expected_completion
    unique_url.save()

    return unique_url


def submit_reform(request, user=None, json_reform_id=None):
    """
    Parses user input data and submits reform

    returns dictionary of arguments intended to be inputs for `save_model`
    """
    fields = dict(request.GET)
    fields.update(dict(request.POST))
    fields = {k: v[0] if isinstance(v, list) else v for k, v in fields.items()}
    start_year = fields.get('start_year', START_YEAR)
    # TODO: migrate first_year to start_year to get rid of weird stuff like
    # this
    fields['first_year'] = fields['start_year']
    has_errors = make_bool(fields['has_errors'])

    # get files from the request object
    request_files = request.FILES

    # which file to use, front-end not yet implemented
    use_puf_not_cps = fields.get('use_puf_not_cps', True)
    assert use_puf_not_cps

    # declare a bunch of variables--TODO: clean this up
    no_inputs = False
    taxcalc_errors = False
    taxcalc_warnings = False
    is_valid = True
    has_parse_errors = False
    errors_warnings = {'warnings': {}, 'errors': {}}
    reform_dict = {}
    assumptions_dict = {}
    reform_text = ""
    assumptions_text = ""
    personal_inputs = None
    model = None
    is_file = False
    submitted_ids = None
    max_q_length = None
    # Assume we do the full calculation unless we find out otherwise
    do_full_calc = False if fields.get('quick_calc') else True
    if do_full_calc and 'full_calc' in fields:
        del fields['full_calc']
    elif 'quick_calc' in fields:
        del fields['quick_calc']
    # re-submission of file for case where file-input generated warnings
    if json_reform_id:
        try:
            json_reform = JSONReformTaxCalculator.objects.get(id=int(json_reform_id))
        except Exception as e:
            msg = "ID {} is not in JSON reform database".format(json_reform_id)
            http_response = HttpResponse(msg, status=400)
            return {'HttpResponse': http_response,
                    'has_errors': True}

        reform_dict = json.loads(json_reform.reform_text)
        assumptions_dict = json.loads(json_reform.assumption_text)
        reform_text = json_reform.raw_reform_text
        assumptions_text = json_reform.raw_assumption_text
        errors_warnings = json.loads(json_reform.errors_warnings_text)

        if "docfile" in request_files or "assumpfile" in request_files:
            if "docfile" in request_files or len(reform_text) == 0:
                reform_text = None
            if "assumpfile" in request_files or len(assumptions_text) == 0:
                assumptions_text = None

            (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings) = get_reform_from_file(request_files,
                                                        reform_text,
                                                        assumptions_text)

            json_reform.reform_text = json.dumps(reform_dict)
            json_reform.assumption_text = json.dumps(assumptions_dict)
            json_reform.raw_reform_text = reform_text
            json_reform.raw_assumption_text = assumptions_text
            json_reform.errors_warnings_text = json.dumps(errors_warnings)
            json_reform.save()

            has_errors = False

    else: # fresh file upload or GUI run
        if 'docfile' in request_files:
            is_file = True
            (reform_dict, assumptions_dict, reform_text, assumptions_text,
                errors_warnings) = get_reform_from_file(request_files)
        else:
            personal_inputs = TaxBrainForm(start_year, fields)
            # If an attempt is made to post data we don't accept
            # raise a 400
            if personal_inputs.non_field_errors():
                return {'HttpResponse': HttpResponse("Bad Input!", status=400),
                        'has_errors': True}
            is_valid = personal_inputs.is_valid()
            if is_valid:
                model = personal_inputs.save()
                # model.set_fields()
                (reform_dict, assumptions_dict, reform_text, assumptions_text,
                    errors_warnings) = get_reform_from_gui(fields,
                                                           taxbrain_model=model)

        json_reform = JSONReformTaxCalculator(
            reform_text=json.dumps(reform_dict),
            assumption_text=json.dumps(assumptions_dict),
            raw_reform_text=reform_text,
            raw_assumption_text=assumptions_text,
            errors_warnings_text=json.dumps(errors_warnings)
        )
        json_reform.save()

    if reform_dict == {}:
        no_inputs = True
    # TODO: account for errors
    # 5 cases:
    #   0. no warning/error messages --> run model
    #   1. has seen warning/error messages and now there are no errors -- > run model
    #   2. has not seen warning/error messages --> show warning/error messages
    #   3. has seen warning/error messages and there are still error messages
    #        --> show warning/error messages again
    #   4. no user input --> do not run model

    warn_msgs = errors_warnings['warnings'] != {}
    stop_errors = no_inputs or not is_valid or errors_warnings['errors'] != {}
    stop_submission = stop_errors or (not has_errors and warn_msgs)
    if stop_submission:
        taxcalc_errors = True if errors_warnings['errors'] else False
        taxcalc_warnings = True if errors_warnings['warnings'] else False
        if personal_inputs is not None:
            # TODO: parse warnings for file_input
            # only handle GUI errors for now
            if ((taxcalc_errors or taxcalc_warnings)
                    and personal_inputs is not None):
                append_errors_warnings(
                    errors_warnings,
                    lambda param, msg: personal_inputs.add_error(param, msg)
                )
            has_parse_errors = any(['Unrecognize value' in e[0]
                                    for e in personal_inputs.errors.values()])
            if no_inputs:
                personal_inputs.add_error(
                    None,
                    "Please specify a tax-law change before submitting."
                )
            if taxcalc_warnings or taxcalc_errors:
                msg = OUT_OF_RANGE_ERROR_MSG
                personal_inputs.add_error(None, msg)
            if has_parse_errors:
                msg = ("Some fields have unrecognized values. Enter comma "
                       "separated values for each input.")
                personal_inputs.add_error(None, msg)
    else:
        log_ip(request)
        user_mods = dict({'policy': reform_dict}, **assumptions_dict)
        data = {'user_mods': json.dumps(user_mods),
                'first_budget_year': int(start_year),
                'start_budget_year': 0}
        if do_full_calc:
            data['num_budget_years'] = NUM_BUDGET_YEARS
            submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(
                data
            )
        else:
            data['num_budget_years'] = NUM_BUDGET_YEARS_QUICK
            submitted_ids, max_q_length = dropq_compute.submit_dropq_small_calculation(
                data
            )

    return {'personal_inputs': personal_inputs,
            'json_reform': json_reform,
            'model': model,
            'stop_submission': stop_submission,
            'has_errors': any([taxcalc_errors, taxcalc_warnings,
                               no_inputs, not is_valid]),
            'errors_warnings': errors_warnings,
            'start_year': start_year,
            'do_full_calc': do_full_calc,
            'is_file': is_file,
            'reform_dict': reform_dict,
            'assumptions_dict': assumptions_dict,
            'reform_text': reform_text,
            'assumptions_text': assumptions_text,
            'submitted_ids': submitted_ids,
            'max_q_length': max_q_length}


def process_reform(request, user=None, **kwargs):
    """
    Submits TaxBrain reforms.  This handles data from the GUI interface
    and the file input interface.  With some tweaks this model could be used
    to submit reforms for all PolicyBrain models

    returns OutputUrl object with parsed user input and warning/error messages
            if necessary
            boolean variable indicating whether this reform has errors or not

    """
    args = submit_reform(request, user=user, **kwargs)
    if 'HttpResponse' in args:
        return args['HttpResponse'], None, args['has_errors'], None

    args['request'] = request
    args['user'] = user
    args['url'] = None
    errors_warnings = args.pop("errors_warnings")
    if args['stop_submission']:
        return (args['personal_inputs'], args['json_reform'], args['has_errors'],
                errors_warnings)
    else:
        del args['stop_submission']
        del args['personal_inputs']
        url = save_model(**args)
        return url, args['json_reform'], args['has_errors'], errors_warnings


def file_input(request):
    """
    Receive request from file input interface and returns parsed data or an
    input form
    """
    form_id = request.POST.get('form_id', None)
    if form_id == 'None':
        form_id = None

    start_year = START_YEAR
    errors = []
    has_errors = False
    if request.method == 'POST':
        # save start_year
        start_year = request.GET['start_year']
        # File is not submitted
        if 'docfile' not in dict(request.FILES) and form_id is None:
            errors = ["Please specify a tax-law change before submitting."]
            json_reform = None
        else:
            (obj, json_reform, has_errors,
                errors_warnings) = process_reform(
                request,
                json_reform_id=form_id
            )
            if has_errors and isinstance(obj, HttpResponse):
                return obj
            else:
                unique_url = obj

            # Case 1: has_errors is True and there are warning/error messages
            #         --> display errors
            # Case 2: has_errors is False and there are warning messages
            #         --> run model (user has already seen warning messages)
            # Case 3: has_errors is False and there are no warning/error messages
            #         --> run model
            if (has_errors and
               (errors_warnings['warnings'] or errors_warnings['errors'])):
                errors.append(OUT_OF_RANGE_ERROR_MSG)
                append_errors_warnings(
                    errors_warnings,
                    lambda _, msg: errors.append(msg)
                )
            else:
                return redirect(unique_url)
    else:
        # GET request, load a default form
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        json_reform = None

    init_context = {
        'form_id': json_reform.id if json_reform is not None else None,
        'errors': errors,
        'has_errors': has_errors,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'params': None,
        'start_years': START_YEARS,
        'start_year': start_year,
        'enable_quick_calc': ENABLE_QUICK_CALC,
        'input_type': "file"
    }

    return render(request, 'taxbrain/input_file.html', init_context)


def personal_results(request):
    """
    Receive data from GUI interface and returns parsed data or default data if
    get request
    """
    start_year = START_YEAR
    has_errors = False
    use_puf_not_cps = True
    if request.method=='POST':
        obj, _, has_errors, _ = process_reform(request)

        # case where validation failed in forms.TaxBrainForm
        # TODO: assert HttpResponse status is 404
        if has_errors and isinstance(obj, HttpResponse):
            return obj

        # No errors--submit to model
        if not has_errors:
            return redirect(obj)
        # Errors from taxcalc.tbi.reform_warnings_errors
        else:
            personal_inputs = obj
            start_year = personal_inputs._first_year


    else:
        # Probably a GET request, load a default form
        print('get get', request.GET)
        print('get post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        personal_inputs = TaxBrainForm(first_year=start_year)
    init_context = {
        'form': personal_inputs,
        'params': nested_form_parameters(int(start_year), use_puf_not_cps),
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
    #TODO: get this function to work with process_reform
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = TaxSaveInputs.objects.get(pk=url.model_pk)
    start_year = dict(model.__dict__)['first_year']
    # This will be a new model instance so unset the primary key
    model.pk = None
    # Unset the computed results, set quick_calc to False
    # (this new model instance will be saved in process_model)
    model.job_ids = None
    model.jobs_not_ready = None
    model.quick_calc = False
    model.tax_result = None

    log_ip(request)

    # get microsim data
    is_file = model.json_text is not None
    json_reform = model.json_text
    # necessary for simulations before PR 641
    if not is_file:
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = get_reform_from_gui(
                request,
                taxbrain_model=model,
                behavior_model=None
        )
        json_reform = JSONReformTaxCalculator(
            reform_text=json.dumps(reform_dict),
            assumption_text=json.dumps(assumptions_dict),
            raw_reform_text=reform_text,
            raw_assumption_text=assumptions_text
        )
        json_reform.save()
    else:
        reform_dict = json.loads(model.json_text.reform_text)
        assumptions_dict = json.loads(model.json_text.assumption_text)

    user_mods = dict({'policy': reform_dict}, **assumptions_dict)
    data = {'user_mods': json.dumps(user_mods),
            'first_budget_year': int(start_year),
            'start_budget_year': 0,
            'num_budget_years': NUM_BUDGET_YEARS}

    # start calc job
    submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(
        data
    )

    args = {'url': url,
            'request': request,
            'model': model,
            'json_reform': json_reform,
            'has_errors': False,
            'start_year': start_year,
            'do_full_calc': True,
            'is_file': is_file,
            'reform_dict': reform_dict,
            'assumptions_dict': assumptions_dict,
            'reform_text': (model.json_text.raw_reform_text
                            if model.json_text else ""),
            'assumptions_text': (model.json_text.raw_assumption_text
                                 if model.json_text else ""),
            'submitted_ids': submitted_ids,
            'max_q_length': max_q_length,
            'user': None}

    url = save_model(**args)

    return redirect(url)


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

    form_personal_exemp = TaxBrainForm(first_year=start_year, instance=model)

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': nested_form_parameters(int(start_year)),
        'taxcalc_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_years': START_YEARS,
        'start_year': str(start_year),
        'is_edit_page': True,
        'has_errors': False
    }

    return render(request, 'taxbrain/input_form.html', init_context)


def add_summary_column(table):
    import copy
    summary = copy.deepcopy(table["cols"][-1])
    summary["label"] = "Total"
    table["cols"].append(summary)
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
    output = model.get_tax_result()
    first_year = model.first_year
    quick_calc = model.quick_calc
    created_on = model.creation_date
    if 'fiscal_tots' in output:
        # Use new key/value pairs for old data
        output['aggr_d'] = output['fiscal_tots']
        output['aggr_1'] = output['fiscal_tots']
        output['aggr_2'] = output['fiscal_tots']
        del output['fiscal_tots']

    tables = taxcalc_results_to_tables(output, first_year)
    tables["tooltips"] = {
        'distribution': DISTRIBUTION_TOOLTIP,
        'difference': DIFFERENCE_TOOLTIP,
        'payroll': PAYROLL_TOOLTIP,
        'income': INCOME_TOOLTIP,
        'base': BASE_TOOLTIP,
        'reform': REFORM_TOOLTIP,
        'bins': INCOME_BINS_TOOLTIP,
        'deciles': INCOME_DECILES_TOOLTIP,
        'fiscal_current_law': FISCAL_CURRENT_LAW,
        'fiscal_reform': FISCAL_REFORM,
        'fiscal_change': FISCAL_CHANGE,
    }

    if (model.json_text is not None and (model.json_text.raw_reform_text or
       model.json_text.raw_assumption_text)):
        reform_file_contents = model.json_text.raw_reform_text
        reform_file_contents = reform_file_contents.replace(" ","&nbsp;")
        assump_file_contents = model.json_text.raw_assumption_text
        assump_file_contents = assump_file_contents.replace(" ","&nbsp;")
    else:
        reform_file_contents = False
        assump_file_contents = False

    if hasattr(request, 'user'):
        is_registered = True if request.user.is_authenticated() else False
    else:
        is_registered = False

    # TODO: Fix the java script mapping problem.  There exists somewhere in
    # the taxbrain javascript code a mapping to the old table names.  As
    # soon as this is changed to accept the new table names, this code NEEDS
    # to be removed.
    tables['fiscal_change'] = add_summary_column(tables.pop('aggr_d'))
    tables['fiscal_currentlaw'] = add_summary_column(tables.pop('aggr_1'))
    tables['fiscal_reform'] = add_summary_column(tables.pop('aggr_2'))
    tables['mY_dec'] = tables.pop('dist2_xdec')
    tables['mX_dec'] = tables.pop('dist1_xdec')
    tables['df_dec'] = tables.pop('diff_itax_xdec')
    tables['pdf_dec'] = tables.pop('diff_ptax_xdec')
    tables['cdf_dec'] = tables.pop('diff_comb_xdec')
    tables['mY_bin'] = tables.pop('dist2_xbin')
    tables['mX_bin'] = tables.pop('dist1_xbin')
    tables['df_bin'] = tables.pop('diff_itax_xbin')
    tables['pdf_bin'] = tables.pop('diff_ptax_xbin')
    tables['cdf_bin'] = tables.pop('diff_comb_xbin')

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
        'allow_dyn_links': True if not assump_file_contents else False,
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
            if error_msgs:
                error_msg = error_msgs[0]
            else:
                error_msg = "Error: stack trace for this error is unavailable"
            val_err_idx = error_msg.rfind("Error")
            error = ErrorMessageTaxCalculator()
            error_contents = error_msg[val_err_idx:].replace(" ","&nbsp;")
            error.text = error_contents
            error.save()
            model.error_text = error
            model.save()
            return render(request, 'taxbrain/failed.html', {"error_msg": error_contents})


        if all([j == 'YES' for j in jobs_ready]):
            results = dropq_compute.dropq_get_results(normalize(job_ids))
            model.tax_result = results
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

    results = url.unique_inputs.get_tax_result()
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
