
import csv
import pdfkit
import json
import pytz
import os
import tempfile
import re
import traceback
import requests


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
from urllib.parse import urlparse, parse_qs

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
from .helpers import (taxcalc_results_to_tables, format_csv,
                      is_wildcard, convert_val, make_bool,
                      )
from .param_displayers import nested_form_parameters
from .compute import (dropq_compute, MockCompute, JobFailError, NUM_BUDGET_YEARS,
                      NUM_BUDGET_YEARS_QUICK, DROPQ_WORKERS)


from ..constants import (DISTRIBUTION_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, FISCAL_CURRENT_LAW, FISCAL_REFORM,
                         FISCAL_CHANGE, INCOME_BINS_TOOLTIP,
                         INCOME_DECILES_TOOLTIP, START_YEAR, START_YEARS,
                         DATA_SOURCES, DEFAULT_SOURCE, OUT_OF_RANGE_ERROR_MSG,
                         WEBAPP_VERSION, TAXCALC_VERSION)

from ..formatters import get_version
from .param_formatters import (get_reform_from_file, get_reform_from_gui,
                               to_json_reform, append_errors_warnings)
from .submit_data import (PostMeta, BadPost, process_reform, save_model,
                          denormalize, normalize, log_ip,
                          JOB_PROC_TIME_IN_SECONDS)

def file_input(request):
    """
    Receive request from file input interface and returns parsed data or an
    input form
    """
    form_id = request.POST.get('form_id', None)
    if form_id == 'None':
        form_id = None

    start_year = START_YEAR
    data_source = DEFAULT_SOURCE
    errors = []
    has_errors = False
    print('files', request.FILES)
    if request.method == 'POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        # save start_year
        start_year = (request.GET.get('start_year', None) or
                      request.POST.get('start_year', None))
        assert start_year is not None
        data_source = (request.GET.get('data_source', None) or
                       request.POST.get('start_year', None))
        assert data_source is not None

        # File is not submitted
        if 'docfile' not in dict(request.FILES) and form_id is None:
            errors = ["Please specify a tax-law change before submitting."]
            json_reform = None
        else:
            obj, post_meta = process_reform(request, json_reform_id=form_id)
            if isinstance(post_meta, BadPost):
                return post_meta.http_response_404
            else:
                unique_url = obj

            if post_meta.stop_submission:
                errors_warnings = post_meta.errors_warnings
                json_reform = post_meta.json_reform
                has_errors = post_meta.has_errors
                errors.append(OUT_OF_RANGE_ERROR_MSG)
                for project in ['policy', 'behavior']:
                    append_errors_warnings(
                        errors_warnings[project],
                        lambda _, msg: errors.append(msg)
                    )
            else:
                return redirect(unique_url)
    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        if 'data_source' in params and params['data_source'][0] in DATA_SOURCES:
            data_source = params['data_source'][0]

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
        'data_sources': DATA_SOURCES,
        'data_source': data_source,
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
    data_source = DEFAULT_SOURCE
    if request.method=='POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        obj, post_meta = process_reform(request)
        # case where validation failed in forms.TaxBrainForm
        # TODO: assert HttpResponse status is 404
        if isinstance(post_meta, BadPost):
            return post_meta.http_response_404

        # No errors--submit to model
        if not post_meta.stop_submission:
            return redirect(obj)
        # Errors from taxcalc.tbi.reform_warnings_errors
        else:
            personal_inputs = post_meta.personal_inputs
            start_year = post_meta.start_year
            data_source = post_meta.data_source
            if data_source == 'PUF':
                use_puf_not_cps = True
            else:
                use_puf_not_cps = False
            has_errors = post_meta.has_errors

    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        # use puf by default
        use_puf_not_cps = True
        if 'data_source' in params and params['data_source'][0] in DATA_SOURCES:
            data_source = params['data_source'][0]
            if data_source != 'PUF':
                use_puf_not_cps = False

        personal_inputs = TaxBrainForm(first_year=start_year,
                                       use_puf_not_cps=use_puf_not_cps)

    init_context = {
        'form': personal_inputs,
        'params': nested_form_parameters(int(start_year), use_puf_not_cps),
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'data_sources': DATA_SOURCES,
        'data_source': data_source,
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

    model = url.unique_inputs
    start_year = model.start_year
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
        model.set_fields()
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = model.get_model_specs()
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
    print('data source', model.data_source)
    data = {'user_mods': json.dumps(user_mods),
            'first_budget_year': int(start_year),
            'start_budget_year': 0,
            'num_budget_years': NUM_BUDGET_YEARS,
            'use_puf_not_cps': model.use_puf_not_cps}

    # start calc job
    submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(
        data
    )

    post_meta = PostMeta(url=url,
            request=request,
            model=model,
            json_reform=json_reform,
            has_errors=False,
            start_year=start_year,
            data_source=model.data_source,
            do_full_calc=True,
            is_file=is_file,
            reform_dict=reform_dict,
            assumptions_dict=assumptions_dict,
            reform_text=(model.json_text.raw_reform_text
                            if model.json_text else ""),
            assumptions_text=(model.json_text.raw_assumption_text
                                 if model.json_text else ""),
            submitted_ids=submitted_ids,
            max_q_length=max_q_length,
            user=None,
            personal_inputs=None,
            stop_submission=False,
            errors_warnings=None)

    url = save_model(post_meta)

    return redirect(url)


def edit_personal_results(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = url.unique_inputs
    start_year = model.first_year
    model.set_fields()

    msg = ('Field {} has been deprecated. Refer to the Tax-Caclulator '
           'documentation for a sensible replacement.')
    form_personal_exemp = TaxBrainForm(
        first_year=start_year,
        use_puf_not_cps=model.use_puf_not_cps,
        instance=model
    )
    form_personal_exemp.is_valid()
    if model.deprecated_fields is not None:
        for dep in model.deprecated_fields:
            form_personal_exemp.add_error(None, msg.format(dep))

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': nested_form_parameters(int(form_personal_exemp._first_year)),
        'taxcalc_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_years': START_YEARS,
        'start_year': str(form_personal_exemp._first_year),
        'is_edit_page': True,
        'has_errors': False,
        'data_sources': DATA_SOURCES,
        'data_source': model.data_source
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
                'decimals': 1,
                'divisor': 1000000000
            },
            'value': str(row_total),
            'year_values': {}
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
    # TODO: Add row labels for decile and income bin tables to the context here
    # and display these instead of hardcode in the javascript
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
        # try to render table; if failure render not available page
        try:
            context = get_result_context(model, request, url)
        except Exception as e:
            print('Exception rendering pk', pk, e)
            traceback.print_exc()
            edit_href = '/taxbrain/edit/{}/?start_year={}'.format(
                pk,
                model.first_year or START_YEAR # sometimes first_year is None
            )
            not_avail_context = dict(edit_href=edit_href,
                                     **context_vers_disp)
            return render(request, 'taxbrain/not_avail.html', not_avail_context)

        context.update(context_vers_disp)
        context["raw_reform_text"] = model.json_text.raw_reform_text if model.json_text else ""
        context["raw_assumption_text"] = model.json_text.raw_assumption_text if model.json_text else ""
        return render(request, 'taxbrain/results.html', context)
    elif model.error_text:
        return render(request, 'taxbrain/failed.html', {"error_msg": model.error_text.text})
    else:
        if not model.check_hostnames(DROPQ_WORKERS):
            print('bad hostname', model.jobs_not_ready, DROPQ_WORKERS)
            return render_to_response('taxbrain/failed.html')
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
