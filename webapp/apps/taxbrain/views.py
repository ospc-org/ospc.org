from __future__ import print_function
import csv
import pdfkit
import json
import pytz
import os

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['matplotlib', 'matplotlib.pyplot', 'mpl_toolkits',
                'mpl_toolkits.mplot3d', 'pandas']
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
                      is_wildcard, convert_val, make_bool)
from .compute import DropqCompute, MockCompute, JobFailError

dropq_compute = DropqCompute()

from ..constants import (DIAGNOSTIC_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, EXPANDED_TOOLTIP, ADJUSTED_TOOLTIP,
                         FISCAL_CURRENT_LAW, FISCAL_REFORM, FISCAL_CHANGE,
                         INCOME_BINS_TOOLTIP, INCOME_DECILES_TOOLTIP, START_YEAR,
                         START_YEARS)


tcversion_info = taxcalc._version.get_versions()

taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])
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


def benefit_surtax_fixup(request, reform, model):
    """
    Take the incoming POST, the user reform, and the TaxSaveInputs
    model and fixup the switches _0, ..., _6 to one array of 
    bools. Also set the model values correctly based on incoming
    POST
    """
    _ids = ['ID_BenefitSurtax_Switch_' + str(i) for i in range(7)]
    values_from_model = [[reform[_id][0] for _id in _ids]]
    final_values = [[True if _id in request else switch for (switch, _id) in zip(values_from_model[0], _ids)]]
    reform['ID_BenefitSurtax_Switch'] = final_values
    for _id, val in zip(_ids, final_values[0]):
        del reform[_id]
        setattr(model, _id, unicode(val))

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


def passthrough_fixup(request, reform, model):
    """
    Take the individual income tax parameters from the user reform
    and set them as the equivalent pass through tax parameters
    """
    pt_reforms = {}
    for param in reform:
        if param.startswith("II_rt") or param.startswith("II_brk"):
            pt_param = "PT_" + param[3:]
            pt_reforms[pt_param] = reform[param]
            if param.endswith("_cpi"):
                setattr(model, pt_param, reform[param])
            else:
                setattr(model, pt_param, reform[param][0])
    reform.update(pt_reforms)


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


def denormalize(x):
    ans = ["#".join([i[0],i[1]]) for i in x]
    ans = [str(x) for x in ans]
    return ans


def normalize(x):
    ans = [i.split('#') for i in x]
    return ans

def process_model(model, start_year, stored_errors=None, request=None,
                  do_full_calc=True, user=None):
    """
    take data from the model and submit the microsimulation job
    inputs:
        model: a TaxSaveInputs model instance
        stored_errors: a dict of errors from the form or None
        request: a Django request object, or None
        do_full_calc: bool, if True, do the full calculation
        user: instance of User model or None
    returns:
        unique_url: OutputUrl model instance
    """

    if stored_errors and request:
        # Force the entered value on to the model
        for attr in stored_errors:
            setattr(model, attr, request.POST[attr])

    # prepare taxcalc params from TaxSaveInputs model
    curr_dict = dict(model.__dict__)
    growth_fixup(curr_dict)

    for key, value in curr_dict.items():
        if type(value) == type(unicode()):
            curr_dict[key] = [convert_val(x) for x in value.split(',') if x]
        else:
            print("missing this: ", key)

    worker_data = {k:v for k, v in curr_dict.items() if not (v == [] or v == None)}
    if request:
        benefit_surtax_fixup(request.REQUEST, worker_data, model)
        amt_fixup(request.REQUEST, worker_data, model)
        passthrough_fixup(request.REQUEST, worker_data, model)
    # start calc job
    if do_full_calc:
        submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(worker_data, int(start_year))
    else:
        submitted_ids, max_q_length = dropq_compute.submit_dropq_small_calculation(worker_data, int(start_year))

    if not submitted_ids:
        raise JobFailError("couldn't submit ids")
    else:
        job_ids = denormalize(submitted_ids)
        model.job_ids = job_ids
        model.first_year = int(start_year)
        model.quick_calc = not do_full_calc
        model.save()
        unique_url = OutputUrl()
        if user:
            unique_url.user = user
        elif request and request.user.is_authenticated():
            current_user = User.objects.get(pk=request.user.id)
            unique_url.user = current_user

        if unique_url.taxcalc_vers != None:
            pass
        else:
            unique_url.taxcalc_vers = taxcalc_version

        unique_url.unique_inputs = model
        unique_url.model_pk = model.pk
        cur_dt = datetime.datetime.utcnow()
        future_offset = datetime.timedelta(seconds=((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
        expected_completion = cur_dt + future_offset
        unique_url.exp_comp_datetime = expected_completion
        unique_url.save()
        return unique_url

def file_input(request):
    """
    This view handles the JSON input page 
    """
    no_inputs = False
    start_year = START_YEAR
    # Probably a GET request, load a default form

    taxcalc_default_params = default_policy(int(start_year))
    has_errors = False
    errors = None


    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        start_year = request.REQUEST['start_year']
        # Assume we do the full calculation unless we find out otherwise
        fields = dict(request.REQUEST)
        do_full_calc = False if fields.get('quick_calc') else True
        error_messages = {}
        reform_dict = {}
        if 'docfile' in request.FILES:
            inmemfile = request.FILES['docfile']
            text_taxcalc = inmemfile.read().strip()
            reform_dict['taxcalc'] = text_taxcalc
        else:
            error_messages['Tax-Calculator:'] = "No file uploaded."

        if error_messages:
            has_errors = True
            errors = ["{} {}".format(k, v) for k, v in error_messages.items()]
        else:
            try:
                log_ip(request)
                #Submit calculation
                if do_full_calc:
                    submitted_ids, max_q_length = dropq_compute.submit_json_dropq_calculation(reform_dict['taxcalc'], int(start_year))
                else:
                    submitted_ids, max_q_length = dropq_compute.submit_json_dropq_small_calculation(reform_dict['taxcalc'], int(start_year))

                if not submitted_ids:
                    raise JobFailError("couldn't submit ids")
                else:
                    job_ids = denormalize(submitted_ids)
                    json_reform = JSONReformTaxCalculator()
                    json_reform.text = reform_dict['taxcalc']
                    json_reform.save()

                    model = TaxSaveInputs()
                    model.job_ids = job_ids
                    model.json_text = json_reform
                    model.first_year = int(start_year)
                    model.quick_calc = not do_full_calc
                    model.save()
                    unique_url = OutputUrl()
                    if request and request.user.is_authenticated():
                        current_user = User.objects.get(pk=request.user.id)
                        unique_url.user = current_user

                    if unique_url.taxcalc_vers != None:
                        pass
                    else:
                        unique_url.taxcalc_vers = taxcalc_version

                    unique_url.unique_inputs = model
                    unique_url.model_pk = model.pk
                    cur_dt = datetime.datetime.utcnow()
                    future_offset = datetime.timedelta(seconds=((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
                    expected_completion = cur_dt + future_offset
                    unique_url.exp_comp_datetime = expected_completion
                    unique_url.save()

                return redirect(unique_url)

            except JobFailError:
                # Bail here and reload the page until we have a better answer
                pass
    else:
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

    init_context = {
        'params': taxcalc_default_params,
        'errors': errors,
        'taxcalc_version': taxcalc_version,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'enable_quick_calc': ENABLE_QUICK_CALC,
        'input_type': "file"
    }


    return render(request, 'taxbrain/input_file.html', init_context)



def json_input(request):
    """
    This view handles the JSON input page 
    """
    no_inputs = False
    start_year = '2016'
    # Probably a GET request, load a default form
    #form_personal_exemp = PersonalExemptionForm(first_year=start_year)

    taxcalc_default_params = default_policy(int(start_year))
    has_errors = False
    errors = None

    STARTING_TEXT = "Put Calculator JSON reform parameters here."
    text_taxcalc = STARTING_TEXT

    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        start_year = request.REQUEST['start_year']
        text_taxcalc = request.POST['taxcalc'].strip()
        # Assume we do the full calculation unless we find out otherwise
        fields = dict(request.REQUEST)
        do_full_calc = False if fields.get('quick_calc') else True
        error_messages = {}
        reform_dict = {}
        if text_taxcalc and not STARTING_TEXT in text_taxcalc:
            reform_dict['taxcalc'] = text_taxcalc
        else:
            error_messages['Tax-Calculator:'] = "No text found in input box."

        if error_messages:
            has_errors = True
            errors = ["{} {}".format(k, v) for k, v in error_messages.items()]
        else:
            try:
                log_ip(request)
                #Submit calculation
                if do_full_calc:
                    submitted_ids, max_q_length = dropq_compute.submit_json_dropq_calculation(reform_dict['taxcalc'], int(start_year))
                else:
                    submitted_ids, max_q_length = dropq_compute.submit_json_dropq_small_calculation(reform_dict['taxcalc'], int(start_year))

                if not submitted_ids:
                    raise JobFailError("couldn't submit ids")
                else:
                    job_ids = denormalize(submitted_ids)
                    json_reform = JSONReformTaxCalculator()
                    json_reform.text = reform_dict['taxcalc']
                    json_reform.save()

                    model = TaxSaveInputs()
                    model.job_ids = job_ids
                    model.json_text = json_reform
                    model.first_year = int(start_year)
                    model.quick_calc = not do_full_calc
                    model.save()
                    unique_url = OutputUrl()
                    if request and request.user.is_authenticated():
                        current_user = User.objects.get(pk=request.user.id)
                        unique_url.user = current_user

                    if unique_url.taxcalc_vers != None:
                        pass
                    else:
                        unique_url.taxcalc_vers = taxcalc_version

                    unique_url.unique_inputs = model
                    unique_url.model_pk = model.pk
                    cur_dt = datetime.datetime.utcnow()
                    future_offset = datetime.timedelta(seconds=((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
                    expected_completion = cur_dt + future_offset
                    unique_url.exp_comp_datetime = expected_completion
                    unique_url.save()

                return redirect(unique_url)

            except JobFailError:
                no_inputs = True
                form_personal_exemp = personal_inputs

    text = {'taxcalc':text_taxcalc}

    init_context = {
        'params': taxcalc_default_params,
        'input_text': text,
        'errors': errors,
        'taxcalc_version': taxcalc_version,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'enable_quick_calc': ENABLE_QUICK_CALC
    }


    return render(request, 'taxbrain/input_json.html', init_context)


def personal_results(request):
    """
    This view handles the input page and calls the function that
    handles the calculation on the inputs.
    """
    no_inputs = False
    start_year = START_YEAR
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        start_year = request.REQUEST['start_year']
        fields = dict(request.REQUEST)
        # Assume we do the full calculation unless we find out otherwise
        do_full_calc = False if fields.get('quick_calc') else True
        fields['first_year'] = fields['start_year']
        if do_full_calc and 'full_calc' in fields:
            del fields['full_calc']
        elif 'quick_calc' in fields:
            del fields['quick_calc']
        personal_inputs = PersonalExemptionForm(start_year, fields)

        # If an attempt is made to post data we don't accept
        # raise a 400
        if personal_inputs.non_field_errors():
            return HttpResponse("Bad Input!", status=400)

        # Accept the POST if the form is valid, or if the form has errors
        # we don't check again so it is OK if the form is invalid the second
        # time
        if personal_inputs.is_valid() or has_errors:
            stored_errors = None
            if has_errors and personal_inputs.errors:
                msg = ("Form has validation errors, but allowing the user "
                       "to proceed anyway since we already showed them the "
                       "errors once.")
                msg2 = "Dropping these errors {}"
                msg2 = msg2.format(personal_inputs.errors)
                logging.warn(msg)
                logging.warn(msg2)
                stored_errors = dict(personal_inputs._errors)
                personal_inputs._errors = {}

            model = personal_inputs.save()
            try:
                log_ip(request)
                unique_url = process_model(model, start_year, stored_errors, request, do_full_calc)
                return redirect(unique_url)
            except JobFailError:
                no_inputs = True
                form_personal_exemp = personal_inputs
        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = personal_inputs

    else:
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        # Probably a GET request, load a default form
        form_personal_exemp = PersonalExemptionForm(first_year=start_year)

    taxcalc_default_params = default_policy(int(start_year))

    has_errors = False
    if has_field_errors(form_personal_exemp):
        msg = ("Some fields have errors. Values outside of suggested ranges "
               " will be accepted if submitted again from this page.")
        form_personal_exemp.add_error(None, msg)
        has_errors = True

    init_context = {
        'form': form_personal_exemp,
        'params': taxcalc_default_params,
        'taxcalc_version': taxcalc_version,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'enable_quick_calc': ENABLE_QUICK_CALC
    }


    if no_inputs:
        form_personal_exemp.add_error(None, "Please specify a tax-law change before submitting.")

    return render(request, 'taxbrain/input_form.html', init_context)


def submit_micro(request, pk):
    """
    This view handles the re-submission of a previously submitted microsim.
    Its primary purpose is to facilitate a mechanism to submit a full microsim
    job after one has submitted parameters for a 'quick calculation'
    """
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
    #Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)
    inputs = user_inputs[0]['fields']

    form_personal_exemp = PersonalExemptionForm(first_year=start_year, instance=model)
    taxcalc_default_params = default_policy(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': taxcalc_default_params,
        'taxcalc_version': taxcalc_version,
        'start_years': START_YEARS,
        'start_year': str(start_year)

    }

    return render(request, 'taxbrain/input_form.html', init_context)


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

    if model.json_text:
        file_contents = model.json_text.text
        file_contents = file_contents.replace(" ","&nbsp;")
    else:
        file_contents = False

    if hasattr(request, 'user'):
        is_registered = True if request.user.is_authenticated() else False
    else:
        is_registered = False
    tables['fiscal_change'] = tables['fiscal_tot_diffs']
    tables['fiscal_currentlaw'] = tables['fiscal_tot_base']
    tables['fiscal_reform'] = tables['fiscal_tot_ref']
    json_table = json.dumps(tables)

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables': json_table,
        'created_on': created_on,
        'first_year': first_year,
        'quick_calc': quick_calc,
        'is_registered': is_registered,
        'is_micro': True,
        'file_contents': file_contents,
        'allow_dyn_links': allow_dyn_links
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
    if model.tax_result:
        context = get_result_context(model, request, url)
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
                return render_to_response('taxbrain/not_ready.html', {'eta': '100'}, context_instance=RequestContext(request))


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
