import json
import datetime
from urlparse import urlparse, parse_qs
import taxcalc

from django.core.mail import send_mail
from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
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
from .helpers import (default_policy, taxcalc_results_to_tables, format_csv,
                      submit_dropq_calculation, dropq_results_ready, dropq_get_results)



tcversion_info = taxcalc._version.get_versions()

taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

def dynamic_input(request):
    """
    This view handles the dynamic input page and calls the function that
    handles the calculation on the inputs.
    """

    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        dyn_mod_form = DynamicModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)

            for key, value in curr_dict.items():
                print "got this ", key, value

            # start calc job
            start_year = 2015
            submitted_ids = submit_dynamic_calculation(worker_data, int(start_year))
            if not submitted_ids:
                no_inputs = True
                form_personal_exemp = personal_inputs
            else:
                job_ids = denormalize(submitted_ids)
                model.job_ids = job_ids
                model.first_year = int(start_year)
                model.save()
                return redirect('tax_results', model.pk)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = personal_inputs

    else:
        params = parse_qs(urlparse(request.build_absolute_uri()).query)

        # Probably a GET request, load a default form
        form_personal_exemp = PersonalExemptionForm(first_year=start_year)
        # start_year = request['QUERY_STRING']

    ogusa_default_params = macro_default_params(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': ogusa_default_params,
        'taxcalc_version': taxcalc_version,
        'ogusa_version': ogusa_version,
        'start_year': start_year
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    if no_inputs:
        form_personal_exemp.add_error(None, "Please specify a tax-law change before submitting.")

    return render(request, 'taxbrain/input_form.html', init_context)




def dynamic_done(request):
    """
    This view sends an email
    """
    if not request.method=='POST':
        raise Http404

    # Client is giving us the info we need to send email

    email_addr = request.POST['email_address']
    job_id = request.POST['job_id']
    url = "http://www.ospc.org/taxbrain/dynamic/{job}".format(job=job_id)

    send_mail(subject="Your TaxBrain simulation has completed!",
        message = """Hello!

        Good news! Your simulation is done and you can now view the results. Just navigate to
        {url} and have a look!

        Best,
        The TaxBrain Team""".format(url=url),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    response = HttpResponse()

    return response
