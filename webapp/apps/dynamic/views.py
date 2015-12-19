import json
import datetime
from urlparse import urlparse, parse_qs
import taxcalc
import ogusa
import os

from django.core.mail import send_mail
from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404, HttpResponseServerError
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import loader, Context
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.models import User
from django import forms

from djqscsv import render_to_csv_response
from .forms import DynamicInputsModelForm, has_field_errors
from .models import DynamicSaveInputs, DynamicOutputUrl
from ..taxbrain.models import TaxSaveInputs, OutputUrl
from ..taxbrain.views import growth_fixup, benefit_surtax_fixup, make_bool
from .helpers import (default_parameters, submit_ogusa_calculation, job_submitted,
                      ogusa_get_results, ogusa_results_to_tables, success_text,
                      failure_text, normalize, denormalize, strip_empty_lists)


tcversion_info = taxcalc._version.get_versions()
taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

ogversion_info = ogusa._version.get_versions()
ogusa_version = ".".join([ogversion_info['version'],
                         ogversion_info['full-revisionid'][:6]])



@permission_required('taxbrain.view_inputs')
def dynamic_input(request, pk):
    """
    This view handles the dynamic input page and calls the function that
    handles the calculation on the inputs.
    """

    # Only acceptable year for dynamic simulations right now
    start_year=2015
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        fields = dict(request.POST)
        fields['first_year'] = start_year
        strip_empty_lists(fields)
        #dyn_mod_form = DynamicInputsModelForm(request.POST)
        dyn_mod_form = DynamicInputsModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)
            for key, value in curr_dict.items():
                print "got this ", key, value

            # get macrosim data from form
            worker_data = {k:v for k, v in curr_dict.items() if v not in (u'', None, [])}

            # set the start year
            start_year = 2015

            #get microsim data 
            taxbrain_model = OutputUrl.objects.get(pk=pk).unique_inputs
            taxbrain_dict = dict(taxbrain_model.__dict__)
            growth_fixup(taxbrain_dict)
            for key, value in taxbrain_dict.items():
                if type(value) == type(unicode()):
                    try:
                        taxbrain_dict[key] = [float(x) for x in value.split(',') if x]
                    except ValueError:
                        taxbrain_dict[key] = [make_bool(x) for x in value.split(',') if x]
                else:
                    print "missing this: ", key

            microsim_data = {k:v for k, v in taxbrain_dict.items() if not (v == [] or v == None)}
            benefit_surtax_fixup(microsim_data)

            # start calc job
            submitted_id = submit_ogusa_calculation(worker_data, int(start_year), microsim_data)
            if submitted_id:
                model.job_ids = denormalize(submitted_id)
                model.first_year = int(start_year)
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    model.user_email = current_user.email
                else:
                    raise Http404

                model.save()
                job_submitted(model.user_email, model.job_ids)
                return redirect('show_job_submitted', model.pk)

            else:
                raise HttpResponseServerError

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:

        # Probably a GET request, load a default form
        form_personal_exemp = DynamicInputsModelForm(first_year=start_year)
        # start_year = request['QUERY_STRING']

    ogusa_default_params = default_parameters(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': ogusa_default_params,
        'taxcalc_version': taxcalc_version,
        'ogusa_version': ogusa_version,
        'start_year': start_year,
        'pk': pk
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/dynamic_input_form.html', init_context)


def dynamic_finished(request):
    """
    This view sends an email
    """

    job_id = request.GET['job_id']
    status = request.GET['status']
    qs = DynamicSaveInputs.objects.filter(job_ids__contains=job_id)
    dsi = qs[0]
    email_addr = dsi.user_email


    # We know the results are ready so go get them from the server
    job_ids = dsi.job_ids
    submitted_ids = normalize(job_ids)
    result = ogusa_get_results(submitted_ids, status=status)
    dsi.tax_result = result
    dsi.creation_date = datetime.datetime.now()
    dsi.save()

    #Create a new output model instance

    if status == "SUCCESS":
        unique_url = DynamicOutputUrl()
        if request.user.is_authenticated():
            current_user = User.objects.get(pk=request.user.id)
            unique_url.user = current_user
        unique_url.unique_inputs = dsi
        unique_url.model_pk = dsi.pk
        unique_url.save()
        hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
        result_url = "{host}/dynamic/results/{pk}".format(host=hostname, pk=unique_url.pk)
        text = success_text()
        text = text.format(url=result_url)
    elif status == "FAILURE":
        text = failure_text(result['job_fail'])
    else:
        raise ValueError("status must be either 'SUCESS' or 'FAILURE'")

    send_mail(subject="Your TaxBrain simulation has completed!",
        message = text,
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    response = HttpResponse('')

    return response


def show_job_submitted(request, pk):
    """
    This view gives the necessary info to show that a dynamic job was
    submitted.
    """
    model = DynamicSaveInputs.objects.get(pk=pk)
    job_id = model.job_ids
    submitted_ids_and_ips = normalize(job_id)
    submitted_id, submitted_ip = submitted_ids_and_ips[0]
    return render_to_response('dynamic/submitted.html', {'job_id': submitted_id})


def ogusa_results(request, pk):
    """
    This view handles the results page.
    """
    try:
        url = DynamicOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    if url.ogusa_vers != None:
        pass
    else:
        url.ogusa_vers = ogusa_version
        url.save()

    output = url.unique_inputs.tax_result
    first_year = url.unique_inputs.first_year
    created_on = url.unique_inputs.creation_date
    tables = ogusa_results_to_tables(output, first_year)

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables':tables,
        'created_on':created_on,
        'first_year':first_year,
    }

    return render(request, 'dynamic/results.html', context)


