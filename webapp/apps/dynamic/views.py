import json
import datetime
from django.utils import timezone
from urllib.parse import urlparse, parse_qs
import os

import taxcalc


from django.conf import settings
from django.core import serializers
from django.http import (HttpResponseRedirect, HttpResponse, Http404,
                         HttpResponseServerError, JsonResponse)
from django.shortcuts import (redirect, render, render_to_response,
                              get_object_or_404)
from django.template.context import RequestContext
from django.contrib.auth.models import User

from .forms import (DynamicInputsModelForm,
                    has_field_errors, DynamicElasticityInputsModelForm)
from .models import (DynamicSaveInputs, DynamicOutputUrl,
                     DynamicElasticitySaveInputs, DynamicElasticityOutputUrl)
from ..taxbrain.models import (TaxSaveInputs, TaxBrainRun,
                               ErrorMessageTaxCalculator,
                               JSONReformTaxCalculator)
from ..taxbrain.views import dropq_compute
from ..taxbrain.param_formatters import (to_json_reform, get_reform_from_gui,
                                         parse_fields, append_errors_warnings)
from ..taxbrain.helpers import make_bool, json_int_key_encode
from ..core.compute import JobFailError

from ..taxbrain.submit_data import JOB_PROC_TIME_IN_SECONDS

from .helpers import (default_parameters, job_submitted,
                      ogusa_results_to_tables, success_text,
                      failure_text, strip_empty_lists,
                      cc_text_finished, cc_text_failure,
                      dynamic_params_from_model, send_cc_email,
                      elast_results_to_tables,
                      default_elasticity_parameters)
from .helpers import (
    default_parameters,
    job_submitted,
    ogusa_results_to_tables,
    success_text,
    failure_text,
    strip_empty_lists,
    cc_text_finished,
    cc_text_failure,
    dynamic_params_from_model,
    send_cc_email,
    elast_results_to_tables,
    default_elasticity_parameters)

from .compute import DynamicCompute, NUM_BUDGET_YEARS

from ..constants import (DISTRIBUTION_TOOLTIP, DIFFERENCE_TOOLTIP,
                         PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                         REFORM_TOOLTIP, INCOME_BINS_TOOLTIP,
                         INCOME_DECILES_TOOLTIP, START_YEAR, START_YEARS,
                         OUT_OF_RANGE_ERROR_MSG)

from ..formatters import get_version

# Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
import traceback
MOCK_MODULES = []

sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

dynamic_compute = DynamicCompute()

tcversion_info = taxcalc._version.get_versions()
TAXCALC_VERSION = tcversion_info['version']

# TODO: use import ogusa; ogusa.__version__
version_path = os.path.join(os.path.split(__file__)[0], "ogusa_version.json")
with open(version_path, "r") as f:
    ogversion_info = json.load(f)
OGUSA_VERSION = ogversion_info['version']

WEBAPP_VERSION = settings.WEBAPP_VERSION


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


def dynamic_input(request, pk):
    """
    This view handles the dynamic input page and calls the function that
    handles the calculation on the inputs.
    """

    start_year = request.GET.get('start_year')
    form_personal_exemp = DynamicInputsModelForm(first_year=start_year)

    ogusa_default_params = default_parameters(int(start_year))
    disabled_flag = os.environ.get('OGUSA_DISABLED', '')

    init_context = {
        'form': form_personal_exemp,
        'params': ogusa_default_params,
        'taxcalc_version': TAXCALC_VERSION,
        'ogusa_version': OGUSA_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_year': start_year,
        'pk': pk,
        'is_disabled': disabled_flag,
        'not_logged_in': not request.user.is_authenticated()
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/dynamic_input_form.html', init_context)


def dynamic_elasticities(request, pk):
    """
    This view handles the dynamic macro elasticities input page and
    calls the function that handles the calculation on the inputs.
    """
    start_year = START_YEAR
    if request.method == 'POST':
        # Client is attempting to send inputs, validate as form data
        init_fields = dict(request.GET)
        init_fields.update(dict(request.POST))

        fields = {}
        for k, v in list(init_fields.items()):
            if isinstance(v, list):
                v = v[0]
            if not v:
                v = (default_elasticity_parameters(int(start_year))[k]
                     .col_fields[0]
                     .default_value)
            fields[k] = v

        start_year = fields.get('start_year', START_YEAR)
        print(fields)
        # TODO: migrate first_year to start_year to get rid of weird stuff like
        # this
        fields['first_year'] = fields['start_year']
        # use_puf_not_cps set to True by default--doesn't matter for dynamic
        # input page. It is there for API consistency
        dyn_mod_form = DynamicElasticityInputsModelForm(start_year, True,
                                                        fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            gdp_elasticity = float(model.elastic_gdp)

            # get microsim data
            outputsurl = TaxBrainRun.objects.get(pk=pk)
            model.micro_run = outputsurl
            taxbrain_model = outputsurl.inputs
            model.data_source = taxbrain_model.data_source
            # get taxbrain data
            # necessary for simulations before PR 641
            reform_parameters = json_int_key_encode(
                taxbrain_model.upstream_parameters['reform'])
            # empty assumptions dictionary
            assumptions_dict = {"behavior": {},
                                "growdiff_response": {},
                                "consumption": {},
                                "growdiff_baseline": {},
                                "growmodel": {}}

            user_mods = dict({'policy': reform_parameters}, **assumptions_dict)
            data = {'user_mods': user_mods,
                    'gdp_elasticity': gdp_elasticity,
                    'start_year': int(start_year),
                    'use_puf_not_cps': model.use_puf_not_cps}

            # start calc job
            data_list = [dict(year_n=i, **data)
                         for i in range(NUM_BUDGET_YEARS)]
            submitted_ids, max_q_length = (
                dropq_compute.submit_elastic_calculation(data_list))

            if not submitted_ids:
                form_personal_exemp = personal_inputs
            else:
                model.job_ids = submitted_ids
                model.first_year = int(start_year)
                model.save()

                unique_url = DynamicElasticityOutputUrl()
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    unique_url.user = current_user

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
                    seconds=((2 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
                expected_completion = cur_dt + future_offset
                unique_url.exp_comp_datetime = expected_completion
                unique_url.save()
                return redirect('elastic_results', unique_url.pk)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:
        # Probably a GET request, load a default form
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        form_personal_exemp = DynamicElasticityInputsModelForm(
            first_year=start_year,
            use_puf_not_cps=True
        )

    elasticity_default_params = default_elasticity_parameters(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_year': start_year,
        'pk': pk
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/elasticity.html', init_context)


def edit_dynamic_elastic(request, pk):
    """
    This view handles the editing of previously compute elasticity of GDP
    dynamic simulation
    """
    try:
        url = DynamicElasticityOutputUrl.objects.get(pk=pk)
    except BaseException:
        raise Http404

    model = url.unique_inputs
    start_year = model.first_year
    # Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)

    form_personal_exemp = DynamicElasticityInputsModelForm(
        first_year=start_year,
        use_puf_not_cps=model.use_puf_not_cps,
        instance=model
    )
    elasticity_default_params = default_elasticity_parameters(int(start_year))

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': taxcalc_vers_disp,
        'webapp_version': webapp_vers_disp,
        'start_year': str(start_year),
        'pk': model.micro_run.pk
    }

    return render(request, 'dynamic/elasticity.html', init_context)


def dynamic_landing(request, pk):
    """
    This view gives a landing page to choose a type of dynamic simulation that
    is linked to the microsim
    """

    outputsurl = TaxBrainRun.objects.get(pk=pk)
    include_ogusa = True
    init_context = {
        'pk': pk,
        'is_authenticated': request.user.is_authenticated(),
        'include_ogusa': include_ogusa,
        'start_year': outputsurl.inputs.start_year,
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION
    }

    return render_to_response('dynamic/landing.html', init_context)


def elastic_results(request, pk):
    """
    This view handles the results page.
    """
    try:
        url = DynamicElasticityOutputUrl.objects.get(pk=pk)
    except BaseException:
        raise Http404

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'taxcalc_version': taxcalc_vers_disp,
                         'webapp_version': webapp_vers_disp}

    model = url.unique_inputs
    if model.tax_result:
        output = model.tax_result
        first_year = model.first_year
        created_on = model.creation_date
        tables = elast_results_to_tables(output, first_year)
        microsim_url = "/taxbrain/" + str(url.unique_inputs.micro_run.pk)

        context = {
            'locals': locals(),
            'unique_url': url,
            'taxcalc_version': taxcalc_vers_disp,
            'webapp_version': webapp_vers_disp,
            'tables': tables,
            'created_on': created_on,
            'first_year': first_year,
            'microsim_url': microsim_url
        }

        return render(request, 'dynamic/elasticity_results.html', context)

    else:
        job_ids = model.job_ids
        jobs_to_check = model.jobs_not_ready
        if not jobs_to_check:
            jobs_to_check = job_ids
        else:
            jobs_to_check = jobs_to_check

        try:
            jobs_ready = dropq_compute.results_ready(jobs_to_check)
        except JobFailError as jfe:
            print(jfe)
            return render_to_response('taxbrain/failed.html')

        if any([j == 'FAIL' for j in jobs_ready]):
            failed_jobs = [sub_id for (sub_id, job_ready)
                           in zip(jobs_to_check, jobs_ready)
                           if job_ready == 'FAIL']

            # Just need the error message from one failed job
            error_msgs = dropq_compute.get_results(
                [failed_jobs[0]], job_failure=True)
            error_msg = error_msgs[0]
            val_err_idx = error_msg.rfind("Error")
            error = ErrorMessageTaxCalculator()
            error_contents = error_msg[val_err_idx:].replace(" ", "&nbsp;")
            error.text = error_contents
            error.save()
            model.error_text = error
            model.save()
            return render(request, 'taxbrain/failed.html',
                          {"error_msg": error_contents})

        if all([job == 'YES' for job in jobs_ready]):
            model.tax_result = dropq_compute.elastic_get_results(job_ids)
            model.creation_date = timezone.now()
            model.save()
            return redirect(url)

        else:
            jobs_not_ready = [sub_id for (sub_id, job_ready)
                              in zip(jobs_to_check, jobs_ready)
                              if not job_ready == 'YES']
            jobs_not_ready = jobs_not_ready
            model.jobs_not_ready = jobs_not_ready
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
                    return JsonResponse({'eta': exp_num_minutes}, status=202)
                else:
                    return JsonResponse({'eta': exp_num_minutes}, status=200)

            else:
                print("rendering not ready yet")
                context = {'eta': '100'}
                context.update(context_vers_disp)
                return render_to_response(
                    'dynamic/not_ready.html',
                    context,
                    context_instance=RequestContext(request))
