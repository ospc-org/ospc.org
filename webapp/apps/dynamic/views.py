import json
import datetime
from urlparse import urlparse, parse_qs
import taxcalc
import ogusa

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
from .helpers import (default_parameters, submit_ogusa_calculation, job_submitted,
                      ogusa_get_results, ogusa_results_to_tables, success_text,
                      failure_text)


tcversion_info = taxcalc._version.get_versions()
taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

ogversion_info = ogusa._version.get_versions()
ogusa_version = ".".join([ogversion_info['version'],
                         ogversion_info['full-revisionid'][:6]])


def denormalize(x):
    ans = ["#".join([i[0],i[1]]) for i in x]
    ans = [str(x) for x in ans]
    return ans


def normalize(x):
    ans = [i.split('#') for i in x]
    return ans



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
        #dyn_mod_form = DynamicInputsModelForm(request.POST)
        dyn_mod_form = DynamicInputsModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)

            for key, value in curr_dict.items():
                print "got this ", key, value

            worker_data = {k:v for k, v in curr_dict.items() if not (v == [] or v == None)}
            # start calc job
            start_year = 2015
            submitted_id = submit_ogusa_calculation(worker_data, int(start_year))
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

    import pdb;pdb.set_trace()
    job_id = request.GET['job_id']
    qs = DynamicSaveInputs.objects.filter(job_ids__contains=job_id)
    dsi = qs[0]
    email_addr = dsi.user_email


    # We know the results are ready so go get them from the server
    job_ids = dsi.job_ids
    submitted_ids = normalize(job_ids)
    try:
        result = ogusa_get_results(submitted_ids)
        dsi.tax_result = result
    except JobFailureException as je:
        text = failure_text()

    except UnknownStatusException as use:
        print "Got an unknown response from server: ", use
        raise use
    else:
        text = success_text()
    finally:
        dsi.creation_date = datetime.datetime.now()
        dsi.save()

    #Create a new output model instance
    unique_url = DynamicOutputUrl()
    if request.user.is_authenticated():
        current_user = User.objects.get(pk=request.user.id)
        unique_url.user = current_user
    unique_url.unique_inputs = dsi
    unique_url.model_pk = dsi.pk
    unique_url.save()

    result_url = "http://www.ospc.org/dynamic/results/{pk}".format(pk=unique_url.pk)

    send_mail(subject="Your TaxBrain simulation has completed!",
        message = text.format(url=result_url),
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
    submitted_id = normalize(job_id)
    return render_to_response('dynamic/submitted.html', {'job_id': submitted_id[0]})


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


