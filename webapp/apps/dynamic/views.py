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
from .helpers import default_parameters


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

    import pdb;pdb.set_trace()
    # Only acceptable year for dynamic simulations right now
    start_year=2015
    if request.method=='POST':
        import pdb;pdb.set_trace()
        # Client is attempting to send inputs, validate as form data
        dyn_mod_form = DynamicInputsModelForm(request.POST)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)

            for key, value in curr_dict.items():
                print "got this ", key, value

            # start calc job
            start_year = 2015
            submitted_id = submit_dynamic_calculation(worker_data, int(start_year))
            if submitted_id:
                model.job_ids = denormalize(submitted_id)
                model.first_year = int(start_year)
                model.save()
                return redirect('show_job_submitted', model.pk)

            else:
                raise HttpResponseServerError

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:

        # Probably a GET request, load a default form
        form_personal_exemp = DynamicInputsModelForm()
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


def show_job_submitted(request, pk):
    """
    This view gives the necessary info to show that a dynamic job was
    submitted.
    """
    import pdb;pdb.set_trace()
    model = DynamicSaveInputs.objects.get(pk=pk)
    job_id = model.job_ids
    submitted_id = normalize(job_id)
    return render_to_response('dynamic/submitted.html', {'job_id': submitted_id[0]})



