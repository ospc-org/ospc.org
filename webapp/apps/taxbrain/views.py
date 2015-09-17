import csv
import pdfkit
import json
import taxcalc
import dropq
import datetime

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

from djqscsv import render_to_csv_response

from .forms import PersonalExemptionForm
from .models import TaxSaveInputs, OutputUrl
from .helpers import (TAXCALC_DEFAULT_PARAMS, taxcalc_results_to_tables, format_csv,
                      submit_dropq_calculation, dropq_results_ready, dropq_get_results)


tcversion_info = taxcalc._version.get_versions()

taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

@permission_required('taxbrain.view_inputs')
def personal_results(request):
    """
    This view handles the input page and calls the function that
    handles the calculation on the inputs.
    """
    no_inputs = False
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        personal_inputs = PersonalExemptionForm(request.POST)

        if personal_inputs.is_valid():
            model = personal_inputs.save()

            # prepare taxcalc params from TaxSaveInputs model
            curr_dict = model.__dict__

            for key, value in curr_dict.items():
                if type(value) == type(unicode()):
                    curr_dict[key] = [float(x) for x in value.split(',') if x]

            worker_data ={k:v for k, v in curr_dict.items() if not (v == [] or v == None)}

            # start calc job
            submitted_ids = submit_dropq_calculation(worker_data)
            if not submitted_ids:
                no_inputs = True
                form_personal_exemp = personal_inputs
            else:
                request.session['submitted_ids'] = submitted_ids
                return redirect('tax_results', model.pk)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = personal_inputs

    else:
        # Probably a GET request, load a default form
        form_personal_exemp = PersonalExemptionForm()

    init_context = {
        'form': form_personal_exemp,
        'params': TAXCALC_DEFAULT_PARAMS,
        'taxcalc_version': taxcalc_version,
    }

    if no_inputs is True:
        init_context['message'] = "Please specify a tax-law change before submitting."

    return render(request, 'taxbrain/input_form.html', init_context)


@permission_required('taxbrain.view_inputs')
def edit_personal_results(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = TaxSaveInputs.objects.get(pk=url.model_pk)
    #Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)
    inputs = user_inputs[0]['fields']

    form_personal_exemp = PersonalExemptionForm(
                        initial=inputs)

    init_context = {
        'form': form_personal_exemp,
        'params': TAXCALC_DEFAULT_PARAMS,
        'taxcalc_version': taxcalc_version,
    }

    return render(request, 'taxbrain/input_form.html', init_context)



@permission_required('taxbrain.view_inputs')
def tax_results(request, pk):
    """
    This view allows the app to wait for the taxcalc results to be
    returned.
    """
    submitted_ids = request.session['submitted_ids']
    if dropq_results_ready(submitted_ids):
        model = TaxSaveInputs.objects.get(pk=pk)
        model.tax_result = dropq_get_results(submitted_ids)

        model.creation_date = datetime.datetime.now()
        model.save()

        current_user = User.objects.get(pk=request.user.id)
        unique_url = OutputUrl()
        unique_url.unique_inputs = model
        unique_url.model_pk = model.pk
        unique_url.user = current_user
        unique_url.save()

        return redirect(unique_url)

    return render_to_response('taxbrain/not_ready.html', {'raw_results':'raw_results'})

@permission_required('taxbrain.view_inputs')
def output_detail(request, pk):
    """
    This view handles the results page.
    """
    try:
        url = OutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    if url.taxcalc_vers != None:
        pass
    else:
        url.taxcalc_vers = taxcalc_version
        url.save()

    output = url.unique_inputs.tax_result
    created_on = url.unique_inputs.creation_date
    tables = taxcalc_results_to_tables(output)
    inputs = url.unique_inputs

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables':tables,
        'created_on':created_on
    }

    return render(request, 'taxbrain/results.html', context)

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
    csv_results = format_csv(results, pk)
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
