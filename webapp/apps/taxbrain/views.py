import csv
import pdfkit
import json
import pytz

#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['numba', 'numba.jit', 'numba.vectorize', 'numba.guvectorize',
                'matplotlib', 'matplotlib.pyplot', 'mpl_toolkits', 'mpl_toolkits.mplot3d']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)


import taxcalc
import dropq
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
from .models import TaxSaveInputs, OutputUrl
from .helpers import default_policy, taxcalc_results_to_tables, format_csv
from .compute import DropqCompute, MockCompute

dropq_compute = DropqCompute()

from .constants import (DIAGNOSTIC_TOOLTIP, DIFFERENCE_TOOLTIP,
                        PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                        REFORM_TOOLTIP, EXPANDED_TOOLTIP, ADJUSTED_TOOLTIP,
                        INCOME_BINS_TOOLTIP, INCOME_DECILES_TOOLTIP)


tcversion_info = taxcalc._version.get_versions()

taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])
START_YEARS = ('2013', '2014', '2015', '2016', '2017')
JOB_PROC_TIME_IN_SECONDS = 30

def benefit_surtax_fixup(mod):
    _ids = ['ID_BenefitSurtax_Switch_' + str(i) for i in range(7)]
    mod['ID_BenefitSurtax_Switch'] = [[mod[_id][0] for _id in _ids]]
    for _id in _ids:
        del mod[_id]

def make_bool(x):
    b = True if x == 'True' else False
    return b

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


def personal_results(request):
    """
    This view handles the input page and calls the function that
    handles the calculation on the inputs.
    """
    no_inputs = False
    start_year = '2016'
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        # Need need to the pull the start_year out of the query string
        # to properly set up the Form
        has_errors = make_bool(request.POST['has_errors'])
        start_year = request.REQUEST['start_year']
        fields = dict(request.REQUEST)
        fields['first_year'] = fields['start_year']
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
            if stored_errors:
                # Force the entered value on to the model
                for attr in stored_errors:
                    setattr(model, attr, request.POST[attr])

            # prepare taxcalc params from TaxSaveInputs model
            curr_dict = dict(model.__dict__)
            growth_fixup(curr_dict)

            for key, value in curr_dict.items():
                if type(value) == type(unicode()):
                    try:
                        curr_dict[key] = [float(x) for x in value.split(',') if x]
                    except ValueError:
                        curr_dict[key] = [make_bool(x) for x in value.split(',') if x]
                else:
                    print "missing this: ", key

            worker_data = {k:v for k, v in curr_dict.items() if not (v == [] or v == None)}
            benefit_surtax_fixup(worker_data)
            # About to begin calculation, log event
            ip = get_real_ip(request)
            if ip is not None:
                # we have a real, public ip address for user
                print "BEGIN DROPQ WORK FROM: ", ip
            else:
                # we don't have a real, public ip address for user
                print "BEGIN DROPQ WORK FROM: unknown IP"

            # start calc job
            submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(worker_data, int(start_year))
            if not submitted_ids:
                no_inputs = True
                form_personal_exemp = personal_inputs
            else:
                job_ids = denormalize(submitted_ids)
                model.job_ids = job_ids
                model.first_year = int(start_year)
                model.save()
                unique_url = OutputUrl()
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    unique_url.user = current_user
                if unique_url.taxcalc_vers != None:
                    pass
                else:
                    unique_url.taxcalc_vers = taxcalc_version

                unique_url.unique_inputs = model
                unique_url.model_pk = model.pk
                cur_dt = datetime.datetime.utcnow()
                future_offset = datetime.timedelta(seconds=((1 + max_q_length) * JOB_PROC_TIME_IN_SECONDS))
                expected_completion = cur_dt + future_offset
                print "expected completion is ", expected_completion
                unique_url.exp_comp_datetime = expected_completion
                unique_url.save()
                return redirect(unique_url)

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
        'has_errors': has_errors
    }


    if no_inputs:
        form_personal_exemp.add_error(None, "Please specify a tax-law change before submitting.")

    return render(request, 'taxbrain/input_form.html', init_context)


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
        output = url.unique_inputs.tax_result
        first_year = url.unique_inputs.first_year
        created_on = url.unique_inputs.creation_date
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
            'deciles': INCOME_DECILES_TOOLTIP
        }
        inputs = url.unique_inputs
        is_registered = True if request.user.is_authenticated() else False

        context = {
            'locals':locals(),
            'unique_url':url,
            'taxcalc_version':taxcalc_version,
            'tables': json.dumps(tables),
            'created_on': created_on,
            'first_year': first_year,
            'is_registered': is_registered,
            'is_micro': True
        }

        return render(request, 'taxbrain/results.html', context)

    else:

        job_ids = model.job_ids
        jobs_to_check = model.jobs_not_ready
        if not jobs_to_check:
            jobs_to_check = normalize(job_ids)
        else:
            jobs_to_check = normalize(jobs_to_check)
        jobs_ready = dropq_compute.dropq_results_ready(jobs_to_check)
        if all(jobs_ready):
            model.tax_result = dropq_compute.dropq_get_results(normalize(job_ids))
            model.creation_date = datetime.datetime.now()
            model.save()
            return redirect(url)
        else:
            jobs_not_ready = [sub_id for (sub_id, job_ready) in
                                zip(jobs_to_check, jobs_ready) if not job_ready]
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
                    return JsonResponse({'eta': 0}, status=200)

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
