import json
import traceback
#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['matplotlib', 'matplotlib.pyplot', 'mpl_toolkits',
                'mpl_toolkits.mplot3d']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

import btax
import taxcalc
import datetime
from django.utils import timezone
import logging
from os import path
from urllib.parse import urlparse, parse_qs
from ipware.ip import get_real_ip

from django.core import serializers
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, render_to_response
from django.template.context import RequestContext
from django.contrib.auth.models import User

from .forms import BTaxExemptionForm, has_field_errors
from .models import BTaxOutputUrl
from .helpers import (get_btax_defaults,
                      BTAX_BITR, BTAX_DEPREC,
                      BTAX_OTHER, BTAX_ECON,
                      group_args_to_btax_depr, hover_args_to_btax_depr,
                      make_bool, convert_val)
from ..taxbrain.helpers import (format_csv,
                                is_wildcard)
from ..taxbrain.views import denormalize, normalize
from .compute import BTAX_WORKERS, DropqComputeBtax, JobFailError

from ..constants import (METTR_TOOLTIP, METR_TOOLTIP, COC_TOOLTIP, DPRC_TOOLTIP,
                        START_YEAR)
from .constants import START_YEARS

from ..formatters import get_version
from django.conf import settings
from .bubble_plot.bubble_plot_tabs import bubble_plot_tabs


dropq_compute = DropqComputeBtax()

BTAX_VERSION_INFO = btax._version.get_versions()

BTAX_VERSION = BTAX_VERSION_INFO['version']

WEBAPP_VERSION = settings.WEBAPP_VERSION


tcversion_info = taxcalc._version.get_versions()

TAXCALC_VERSION = tcversion_info['version']


JOB_PROC_TIME_IN_SECONDS = 30


def make_bool_gds_ads(form_btax_input):
    for k, v in list(vars(form_btax_input).items()):
        if any(token in k for token in ('gds', 'ads', 'tax')):
            setattr(getattr(form_btax_input, k), 'value', make_bool(v))
    return form_btax_input


def depreciation_fixup(model, request):
    """
    For each row of the tax depreciation schedule,
    get the value of the property, e.g. 'btax_depr_3yr' (which
    indicates which button was selected) and then store that
    value as 'True' on the model itself.
    """
    years = ['3', '5', '7', '10', '15', '20', '25', '27_5', '39']
    for year in years:
        depr_field = "btax_depr_{}yr".format(year)
        if depr_field in request.POST:
            button_value = request.POST[depr_field]
            setattr(model, button_value, "True")
    model.save()


def btax_results(request):
    """
    This view handles the input page and calls the function that
    handles the calculation on the inputs.
    """
    no_inputs = False
    start_year = START_YEAR
    if request.method=='POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        fields = dict(request.GET)
        fields.update(dict(request.POST))
        fields = {k: v[0] if isinstance(v, list) else v for k, v in list(fields.items())}
        start_year = fields.get('start_year', START_YEAR)
        # TODO: migrate first_year to start_year to get rid of weird stuff like
        # this
        fields['first_year'] = fields['start_year']
        btax_inputs = BTaxExemptionForm(start_year, fields)
        btax_inputs = make_bool_gds_ads(btax_inputs)
        # If an attempt is made to post data we don't accept
        # raise a 400
        if btax_inputs.non_field_errors():
            return HttpResponse("Bad Input!", status=400)

        # Accept the POST if the form is valid, or if the form has errors
        # we don't check again so it is OK if the form is invalid the second
        # time

        if btax_inputs.is_valid() or has_errors:
            print('is valid')
            stored_errors = None
            if has_errors and btax_inputs.errors:
                msg = ("Form has validation errors, but allowing the user "
                       "to proceed anyway since we already showed them the "
                       "errors once.")
                msg2 = "Dropping these errors {}"
                msg2 = msg2.format(btax_inputs.errors)
                logging.warn(msg)
                logging.warn(msg2)
                stored_errors = dict(btax_inputs._errors)
                btax_inputs._errors = {}

            model = btax_inputs.save()
            depreciation_fixup(model, request)

            if stored_errors:
                # Force the entered value on to the model
                for attr in stored_errors:
                    setattr(model, attr, request.POST[attr])

            # prepare taxcalc params from BTaxSaveInputs model
            curr_dict = dict(model.__dict__)

            for key, value in list(curr_dict.items()):
                if type(value) == type(str()):
                    curr_dict[key] = [convert_val(x) for x in value.split(',') if x]
                else:
                    print("missing this: ", key)

            worker_data = {k:v for k, v in list(curr_dict.items()) if not (v == [] or v == None)}

            #Non corp entity fix up:
            if 'btax_betr_pass' not in worker_data:
                worker_data['btax_betr_pass'] = [0.0]

            # About to begin calculation, log event
            ip = get_real_ip(request)
            if ip is not None:
                # we have a real, public ip address for user
                print("BEGIN DROPQ WORK FROM: ", ip)
            else:
                # we don't have a real, public ip address for user
                print("BEGIN DROPQ WORK FROM: unknown IP")

            # start calc job
            submitted_ids, max_q_length = dropq_compute.submit_btax_calculation(worker_data, start_year)

            print('submitted_ids', submitted_ids, max_q_length)
            if not submitted_ids:
                no_inputs = True
                form_btax_input = btax_inputs
            else:
                job_ids = denormalize(submitted_ids)
                model.job_ids = job_ids
                model.first_year = int(start_year)
                model.save()
                unique_url = BTaxOutputUrl()
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    unique_url.user = current_user
                if unique_url.btax_vers != None:
                    pass
                else:
                    unique_url.btax_vers = BTAX_VERSION
                if unique_url.taxcalc_vers is not None:
                    pass
                else:
                    unique_url.taxcalc_vers = TAXCALC_VERSION
                if unique_url.webapp_vers is not None:
                    pass
                else:
                    unique_url.webapp_vers = WEBAPP_VERSION

                unique_url.unique_inputs = model
                unique_url.model_pk = model.pk
                cur_dt = timezone.now()
                future_offset = datetime.timedelta(
                                    seconds=((2 + max_q_length)
                                             * JOB_PROC_TIME_IN_SECONDS)
                                )
                expected_completion = cur_dt + future_offset
                unique_url.exp_comp_datetime = expected_completion
                unique_url.save()
                return redirect(unique_url)

        else:
            print('invalid inputs')
            # received POST but invalid results, return to form with errors
            form_btax_input = btax_inputs

    else:
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        # Probably a GET request, load a default form
        form_btax_input = BTaxExemptionForm(first_year=start_year)

    btax_default_params = get_btax_defaults(start_year)
    has_errors = False
    if has_field_errors(form_btax_input):
        msg = ("Some fields have errors. Values outside of suggested ranges "
               " will be accepted if submitted again from this page.")
        form_btax_input.add_error(None, msg)
        has_errors = True
    asset_yr_str = ["3", "5", "7", "10", "15", "20", "25", "27_5", "39"]
    form_btax_input = make_bool_gds_ads(form_btax_input)
    hover_notes = hover_args_to_btax_depr()

    init_context = {
        'form': form_btax_input,
        'make_bool':  make_bool,
        'params': btax_default_params,
        'btax_version': BTAX_VERSION,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
        'asset_yr_str': asset_yr_str,
        'depr_argument_groups': group_args_to_btax_depr(btax_default_params, asset_yr_str),
        'hover_notes': hover_notes,
        'is_btax': True,
    }


    if no_inputs:
        form_btax_input.add_error(None, "Please specify a tax-law change before submitting.")
    return render(request, 'btax/input_form.html', init_context)


def edit_btax_results(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    try:
        url = BTaxOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = url.unique_inputs
    start_year = model.first_year
    #Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)

    form_btax_input = BTaxExemptionForm(first_year=start_year, instance=model)
    btax_default_params = get_btax_defaults()
    has_errors = False
    asset_yr_str = ["3", "5", "7", "10", "15", "20", "25", "27_5", "39"]
    form_btax_input = make_bool_gds_ads(form_btax_input)
    hover_notes = hover_args_to_btax_depr()

    btax_vers_disp = get_version(url, 'btax_vers', BTAX_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'btax_version': btax_vers_disp,
                         'webapp_version': webapp_vers_disp}

    init_context = {
        'form': form_btax_input,
        'make_bool': make_bool,
        'params': btax_default_params,
        'btax_version': btax_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_years': START_YEARS,
        'start_year': str(start_year),
        'has_errors': has_errors,
        'asset_yr_str': asset_yr_str,
        'depr_argument_groups': group_args_to_btax_depr(btax_default_params, asset_yr_str),
        'hover_notes': hover_notes,
        'is_btax': True,

    }

    return render(request, 'btax/input_form.html', init_context)


def get_mock_json(as_str=True):
    here = path.abspath(path.dirname(__file__))
    mock_json_path = path.join(here, 'mock_btax_result.json')

    with open(mock_json_path) as f:
        mock_json = f.read()
    if as_str:
        return mock_json
    return json.loads(mock_json)


def generate_mock_results(request):
    mock_json = get_mock_json()
    context = dict()
    context["tooltips"] = {
        "metr": METR_TOOLTIP,
        "mettr": METTR_TOOLTIP,
        "coc": COC_TOOLTIP,
        "dprc": DPRC_TOOLTIP,
    }
    context.update({
        'btax_version':BTAX_VERSION,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_vers': WEBAPP_VERSION,
        'table_json': str(mock_json),
        'is_btax': True,
    })

    return render(request, 'btax/results.html', context)


def output_detail(request, pk):
    """
    This view is the single page of diplaying a progress bar for how
    close the job is to finishing, and then it will also display the
    job results if the job is done. Finally, it will render a 'job failed'
    page if the job has failed.
    """

    try:
        url = BTaxOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    btax_vers_disp = get_version(url, 'btax_vers', BTAX_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'btax_version': btax_vers_disp,
                         'webapp_version': webapp_vers_disp}

    model = url.unique_inputs
    if model.tax_result:
        # try to render table; if failure render not available page
        try:
            exp_num_minutes = 0.25
            tax_result = url.unique_inputs.tax_result
            tables = json.loads(tax_result)[0]
            first_year = url.unique_inputs.first_year
            created_on = url.unique_inputs.creation_date
            tables["tooltips"] = {
                "metr": METR_TOOLTIP,
                "mettr": METTR_TOOLTIP,
                "coc": COC_TOOLTIP,
                "dprc": DPRC_TOOLTIP,
            }
            bubble_js, bubble_div, cdn_js, cdn_css, widget_js, widget_css = bubble_plot_tabs(tables['dataframes'])
        except Exception as e:
            print('Exception rendering pk', pk, e)
            traceback.print_exc()
            edit_href = '/ccc/edit/{}/?start_year={}'.format(
                pk,
                model.first_year or START_YEAR  # sometimes first_year is None
            )
            print('edit_href', edit_href, pk, model.first_year)
            not_avail_context = dict(edit_href=edit_href,
                                     is_btax=True,
                                     **context_vers_disp)
            return render(request, 'btax/not_avail.html', not_avail_context)

        inputs = url.unique_inputs
        is_registered = True if request.user.is_authenticated() else False
        context = tables.copy()
        context.update({
            'locals': locals(),
            'unique_url': url,
            'table_json': json.dumps(tables),
            'created_on': created_on,
            'first_year': first_year,
            'is_btax': True,
            'bubble_js': bubble_js,
            'bubble_div': bubble_div,
            'cdn_js': cdn_js,
            'cdn_css': cdn_css,
            'widget_js': widget_js,
            'widget_css': widget_css
        })
        context.update(context_vers_disp)
        return render(request, 'btax/results.html', context)

    else:
        if not model.check_hostnames(BTAX_WORKERS):
            print('bad hostname', model.jobs_not_ready, BTAX_WORKERS)
            return render_to_response('taxbrain/failed.html',
                                      context={'is_btax': True})
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
            return render_to_response('taxbrain/failed.html',
                                     context={'is_btax': True})

        if any([j == 'FAIL' for j in jobs_ready]):
            failed_jobs = [sub_id for (sub_id, job_ready) in
                           zip(jobs_to_check, jobs_ready) if job_ready == 'FAIL']

            #Just need the error message from one failed job
            error_msgs = dropq_compute.dropq_get_results([failed_jobs[0]], job_failure=True)
            error_msg = error_msgs[0]
            val_err_idx = error_msg.rfind("Error")
            context = {"error_msg": error_msg[val_err_idx:],
                       "is_btax": True}
            return render(request, 'taxbrain/failed.html', context)



        if all([job == 'YES' for job in jobs_ready]):
            tax_result = dropq_compute.btax_get_results(normalize(job_ids))
            model.tax_result = json.dumps(tax_result)
            model.creation_date = timezone.now()
            print('ready')
            model.save()
            return redirect(url)
        else:
            jobs_not_ready = [sub_id for (sub_id, job_ready) in
                                zip(jobs_to_check, jobs_ready) if not job_ready == 'YES']
            jobs_not_ready = denormalize(jobs_not_ready)
            model.jobs_not_ready = jobs_not_ready
            print('not ready', jobs_not_ready)
            model.save()
            if request.method == 'POST':
                # if not ready yet, insert number of minutes remaining
                exp_comp_dt = url.exp_comp_datetime
                utc_now = timezone.now()
                dt = exp_comp_dt - utc_now
                exp_num_minutes = dt.total_seconds() / 60.
                exp_num_minutes = round(exp_num_minutes, 2)
                exp_num_minutes = exp_num_minutes if exp_num_minutes > 0 else 0
                if exp_num_minutes > 0:
                    return JsonResponse({'eta': exp_num_minutes,'wait_interval': 7000}, status=202)
                else:
                    return JsonResponse({'eta': exp_num_minutes,'wait_interval': 7000}, status=200)

            else:
                print("rendering not ready yet")
                context = {'eta': '100', 'is_btax': True, 'wait_interval': 7000}
                context.update(context_vers_disp)
                return render_to_response('btax/not_ready.html', context,
                                          context_instance=RequestContext(request))
