import json
import datetime
from urlparse import urlparse, parse_qs
import os
#Mock some module for imports because we can't fit them on Heroku slugs
from mock import Mock
import sys
MOCK_MODULES = ['numba', 'numba.jit', 'numba.vectorize', 'numba.guvectorize']

sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)
import taxcalc


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
from .forms import (DynamicInputsModelForm, DynamicBehavioralInputsModelForm, 
                    has_field_errors, DynamicElasticityInputsModelForm)
from .models import (DynamicSaveInputs, DynamicOutputUrl,
                     DynamicBehaviorSaveInputs, DynamicBehaviorOutputUrl,
                     DynamicElasticitySaveInputs, DynamicElasticityOutputUrl)
from ..taxbrain.models import TaxSaveInputs, OutputUrl
from ..taxbrain.views import growth_fixup, benefit_surtax_fixup, make_bool
from ..taxbrain.helpers import default_policy, taxcalc_results_to_tables, default_behavior
from ..taxbrain.compute import DropqCompute

from .helpers import (default_parameters, job_submitted,
                      ogusa_results_to_tables, success_text,
                      failure_text, normalize, denormalize, strip_empty_lists,
                      cc_text_finished, cc_text_failure, dynamic_params_from_model,
                      send_cc_email, default_behavior_parameters,
                      elast_results_to_tables, default_elasticity_parameters)

from .compute import DynamicCompute
dynamic_compute = DynamicCompute()

from ..taxbrain.constants import (DIAGNOSTIC_TOOLTIP, DIFFERENCE_TOOLTIP,
                                  PAYROLL_TOOLTIP, INCOME_TOOLTIP, BASE_TOOLTIP,
                                  REFORM_TOOLTIP, EXPANDED_TOOLTIP,
                                  ADJUSTED_TOOLTIP, INCOME_BINS_TOOLTIP,
                                  INCOME_DECILES_TOOLTIP)



tcversion_info = taxcalc._version.get_versions()
taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])

version_path = os.path.join(os.path.split(__file__)[0], "ogusa_version.json")
with open(version_path, "r") as f:
    ogversion_info = json.load(f)
ogusa_version = ".".join([ogversion_info['version'],
                         ogversion_info['full-revisionid'][:6]])


def dynamic_input(request, pk):
    """
    This view handles the dynamic input page and calls the function that
    handles the calculation on the inputs.
    """

    # Only acceptable year for dynamic simulations right now
    start_year=2015
    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        fields = dict(request.REQUEST)
        fields['first_year'] = start_year
        strip_empty_lists(fields)
        dyn_mod_form = DynamicInputsModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)
            for key, value in curr_dict.items():
                print "got this ", key, value

            # get macrosim data from form
            worker_data = {k:v for k, v in curr_dict.items() if v not in (u'', None, [])}

            #get microsim data
            outputsurl = OutputUrl.objects.get(pk=pk)
            model.micro_sim = outputsurl
            taxbrain_model = outputsurl.unique_inputs
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

            #Don't need to pass around the microsim results
            if 'tax_result' in microsim_data:
                del microsim_data['tax_result']

            benefit_surtax_fixup(microsim_data)

            # start calc job
            submitted_ids, guids = dynamic_compute.submit_ogusa_calculation(worker_data, int(start_year), microsim_data)
            if submitted_ids:
                model.job_ids = denormalize(submitted_ids)
                model.guids = denormalize(guids)
                model.first_year = int(start_year)
                if request.user.is_authenticated():
                    current_user = User.objects.get(pk=request.user.id)
                    model.user_email = current_user.email
                else:
                    raise Http404

                model.save()
                job_submitted(model.user_email, model)
                return redirect('show_job_submitted', model.pk)

            else:
                raise HttpResponseServerError

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:

        # Probably a GET request, load a default form
        start_year = request.REQUEST.get('start_year', start_year)
        form_personal_exemp = DynamicInputsModelForm(first_year=start_year)

    ogusa_default_params = default_parameters(int(start_year))
    disabled_flag = os.environ.get('OGUSA_DISABLED', '')

    init_context = {
        'form': form_personal_exemp,
        'params': ogusa_default_params,
        'taxcalc_version': taxcalc_version,
        'ogusa_version': ogusa_version,
        'start_year': start_year,
        'pk': pk,
        'is_disabled': disabled_flag
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/dynamic_input_form.html', init_context)


def dynamic_behavioral(request, pk):
    """
    This view handles the dynamic behavioral input page and calls the function that
    handles the calculation on the inputs.
    """

    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        fields = dict(request.REQUEST)
        strip_empty_lists(fields)
        start_year = request.GET['start_year']
        fields['first_year'] = start_year
        dyn_mod_form = DynamicBehavioralInputsModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)
            for key, value in curr_dict.items():
                print "got this ", key, value

            for key, value in curr_dict.items():
                if type(value) == type(unicode()):
                    try:
                        curr_dict[key] = [float(x) for x in value.split(',') if x]
                    except ValueError:
                        curr_dict[key] = [make_bool(x) for x in value.split(',') if x]
                else:
                    print "missing this: ", key

            # get macrosim data from form
            worker_data = {k:v for k, v in curr_dict.items() if v not in (u'', None, [])}

            #get microsim data 
            outputsurl = OutputUrl.objects.get(pk=pk)
            model.micro_sim = outputsurl
            taxbrain_model = outputsurl.unique_inputs
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

            #Don't need to pass around the microsim results
            if 'tax_result' in microsim_data:
                del microsim_data['tax_result']

            benefit_surtax_fixup(microsim_data)

            microsim_data.update(worker_data)

            # start calc job
            submitted_ids, max_q_length = dropq_compute.submit_dropq_calculation(microsim_data, int(start_year))
            if not submitted_ids:
                no_inputs = True
                form_personal_exemp = personal_inputs
            else:
                model.job_ids = denormalize(submitted_ids)
                model.first_year = int(start_year)
                model.save()
                return redirect('behavior_results', model.pk)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:

        # Probably a GET request, load a default form
        start_year = request.REQUEST.get('start_year')
        form_personal_exemp = DynamicBehavioralInputsModelForm(first_year=start_year)

    behavior_default_params = default_behavior(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': behavior_default_params,
        'taxcalc_version': taxcalc_version,
        'start_year': start_year,
        'pk': pk
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/behavior.html', init_context)


def dynamic_elasticities(request, pk):
    """
    This view handles the dynamic macro elasticities input page and 
    calls the function that handles the calculation on the inputs.
    """

    # Probably a GET request, load a default form
    start_year = request.REQUEST.get('start_year')
    elasticity_default_params = default_elasticity_parameters(int(start_year))

    if request.method=='POST':
        # Client is attempting to send inputs, validate as form data
        fields = dict(request.REQUEST)
        strip_empty_lists(fields)
        fields['first_year'] = start_year
        dyn_mod_form = DynamicElasticityInputsModelForm(start_year, fields)

        if dyn_mod_form.is_valid():
            model = dyn_mod_form.save()

            curr_dict = dict(model.__dict__)
            for key, value in curr_dict.items():
                print "got this ", key, value

            #Replace empty elasticity field with defaults
            for k,v in elasticity_default_params.items():
                if k in curr_dict and not curr_dict[k]:
                    curr_dict[k] = elasticity_default_params[k].col_fields[0].values

            for key, value in curr_dict.items():
                if type(value) == type(unicode()):
                    try:
                        curr_dict[key] = [float(x) for x in value.split(',') if x]
                    except ValueError:
                        curr_dict[key] = [make_bool(x) for x in value.split(',') if x]
                else:
                    print "missing this: ", key


            # get macrosim data from form
            worker_data = {k:v for k, v in curr_dict.items() if v not in (u'', None, [])}

            #get microsim data 
            outputsurl = OutputUrl.objects.get(pk=pk)
            model.micro_sim = outputsurl
            taxbrain_model = outputsurl.unique_inputs
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

            #Don't need to pass around the microsim results
            if 'tax_result' in microsim_data:
                del microsim_data['tax_result']

            benefit_surtax_fixup(microsim_data)
            microsim_data.update(worker_data)

            # start calc job
            submitted_ids, max_q_length = dropq_compute.submit_elastic_calculation(microsim_data,
                                                                     int(start_year))
            if not submitted_ids:
                no_inputs = True
                form_personal_exemp = personal_inputs
            else:
                model.job_ids = denormalize(submitted_ids)
                model.first_year = int(start_year)
                model.save()
                return redirect('elastic_results', model.pk)

        else:
            # received POST but invalid results, return to form with errors
            form_personal_exemp = dyn_mod_form

    else:

        form_personal_exemp = DynamicElasticityInputsModelForm(first_year=start_year)


    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': taxcalc_version,
        'start_year': start_year,
        'pk': pk
    }

    if has_field_errors(form_personal_exemp):
        form_personal_exemp.add_error(None, "Some fields have errors.")

    return render(request, 'dynamic/elasticity.html', init_context)


def edit_dynamic_behavioral(request, pk):
    """
    This view handles the editing of previously entered inputs
    """
    try:
        url = DynamicBehaviorOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = DynamicBehaviorSaveInputs.objects.get(pk=url.model_pk)
    start_year = model.first_year
    #Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)
    inputs = user_inputs[0]['fields']

    form_personal_exemp = DynamicBehavioralInputsModelForm(first_year=start_year, instance=model)
    behavior_default_params = default_behavior_parameters(int(start_year))

    init_context = {
        'form': form_personal_exemp,
        'params': behavior_default_params,
        'taxcalc_version': taxcalc_version,
        'start_year': str(start_year),
        'pk': model.micro_sim.pk
    }

    return render(request, 'dynamic/behavior.html', init_context)


def edit_dynamic_elastic(request, pk):
    """
    This view handles the editing of previously compute elasticity of GDP
    dynamic simulation
    """
    try:
        url = DynamicElasticityOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    model = DynamicElasticitySaveInputs.objects.get(pk=url.model_pk)
    start_year = model.first_year
    #Get the user-input from the model in a way we can render
    ser_model = serializers.serialize('json', [model])
    user_inputs = json.loads(ser_model)
    inputs = user_inputs[0]['fields']

    form_personal_exemp = DynamicElasticityInputsModelForm(first_year=start_year, instance=model)
    elasticity_default_params = default_elasticity_parameters(int(start_year))


    init_context = {
        'form': form_personal_exemp,
        'params': elasticity_default_params,
        'taxcalc_version': taxcalc_version,
        'start_year': str(start_year),
        'pk': pk
    }

    return render(request, 'dynamic/elasticity.html', init_context)


def dynamic_landing(request, pk):
    """
    This view gives a landing page to choose a type of dynamic simulation that
    is linked to the microsim
    """
    init_context = {
            'pk': pk,
            'is_authenticated': request.user.is_authenticated(),
            'start_year': request.GET['start_year']
             }

    return render_to_response('dynamic/landing.html', init_context)



def dynamic_finished(request):
    """
    This view sends an email to the job submitter that the dynamic job
    is done. It also sends CC emails to the CC list.
    """

    job_id = request.GET['job_id']
    status = request.GET['status']
    qs = DynamicSaveInputs.objects.filter(job_ids__contains=job_id)
    dsi = qs[0]
    email_addr = dsi.user_email

    # We know the results are ready so go get them from the server
    job_ids = dsi.job_ids
    submitted_ids = normalize(job_ids)
    result = dynamic_compute.ogusa_get_results(submitted_ids, status=status)
    dsi.tax_result = result
    dsi.creation_date = datetime.datetime.now()
    dsi.save()

    params = dynamic_params_from_model(dsi)
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    microsim_url = hostname + "/taxbrain/" + str(dsi.micro_sim.pk)
    #Create a new output model instance
    if status == "SUCCESS":
        unique_url = DynamicOutputUrl()
        if request.user.is_authenticated():
            current_user = User.objects.get(pk=request.user.id)
            unique_url.user = current_user
        unique_url.unique_inputs = dsi
        unique_url.model_pk = dsi.pk
        unique_url.save()
        result_url = "{host}/dynamic/results/{pk}".format(host=hostname,
                                                          pk=unique_url.pk)
        text = success_text()
        text = text.format(url=result_url, microsim_url=microsim_url,
                           job_id=job_id, params=params)
        cc_txt, subj_txt = cc_text_finished(url=result_url)

    elif status == "FAILURE":
        text = failure_text()
        text = text.format(traceback=result['job_fail'], microsim_url=microsim_url,
                           job_id=job_id, params=params)

        cc_txt, subj_txt = cc_text_failure(traceback=result['job_fail'])
    else:
        raise ValueError("status must be either 'SUCCESS' or 'FAILURE'")

    send_mail(subject="Your TaxBrain simulation has completed!",
        message = text,
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    send_cc_email(cc_txt, subj_txt, dsi)
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


def elastic_output(request, pk):
    """
    This view handles the results page.
    """
    try:
        url = DynamicElasticityOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    if url.taxcalc_vers != None:
        pass
    else:
        url.taxcalc_vers = taxcalc_version
        url.save()

    output = url.unique_inputs.tax_result
    first_year = url.unique_inputs.first_year
    created_on = url.unique_inputs.creation_date
    tables = elast_results_to_tables(output, first_year)
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    microsim_url = hostname + "/taxbrain/" + str(url.unique_inputs.micro_sim.pk)

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables':tables,
        'created_on':created_on,
        'first_year':first_year,
        'microsim_url':microsim_url
    }


    return render(request, 'dynamic/elasticity_results.html', context)




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
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    microsim_url = hostname + "/taxbrain/" + str(url.unique_inputs.micro_sim.pk)

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables':tables,
        'created_on':created_on,
        'first_year':first_year,
        'microsim_url':microsim_url
    }

    return render(request, 'dynamic/results.html', context)


def elastic_results(request, pk):
    """
    This view allows the app to wait for the taxcalc results to be
    returned.
    """

    model = DynamicElasticitySaveInputs.objects.get(pk=pk)
    job_ids = model.job_ids
    submitted_ids = normalize(job_ids)
    if all(dropq_compute.dropq_results_ready(submitted_ids)):
        model.tax_result = dropq_compute.elastic_get_results(submitted_ids)
        model.creation_date = datetime.datetime.now()
        model.save()

        unique_url = DynamicElasticityOutputUrl()
        if request.user.is_authenticated():
            current_user = User.objects.get(pk=request.user.id)
            unique_url.user = current_user
        unique_url.unique_inputs = model
        unique_url.model_pk = model.pk
        unique_url.save()

        return redirect('elastic_output', unique_url.pk)

    return render_to_response('dynamic/not_ready.html', {'raw_results':'raw_results'})


def behavior_results(request, pk):
    """
    This view allows the app to wait for the taxcalc results to be
    returned.
    """
    model = DynamicBehaviorSaveInputs.objects.get(pk=pk)
    job_ids = model.job_ids
    submitted_ids = normalize(job_ids)
    if all(dropq_compute.dropq_results_ready(submitted_ids)):
        model.tax_result = dropq_compute.dropq_get_results(submitted_ids)
        model.creation_date = datetime.datetime.now()
        model.save()

        unique_url = DynamicBehaviorOutputUrl()
        if request.user.is_authenticated():
            current_user = User.objects.get(pk=request.user.id)
            unique_url.user = current_user
        unique_url.unique_inputs = model
        unique_url.model_pk = model.pk
        unique_url.save()

        return redirect('behavior_output', unique_url.pk)

    return render_to_response('dynamic/not_ready.html', {'raw_results':'raw_results'})


def behavior_output(request, pk):
    """
    This view handles the partial equilibrium results page.
    """
    try:
        url = DynamicBehaviorOutputUrl.objects.get(pk=pk)
    except:
        raise Http404

    if url.taxcalc_vers != None:
        pass
    else:
        url.taxcalc_vers = taxcalc_version
        url.save()

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
    dbsi = url.unique_inputs
    is_registered = True if request.user.is_authenticated() else False
    hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
    microsim_url = hostname + "/taxbrain/" + str(dbsi.micro_sim.pk)

    context = {
        'locals':locals(),
        'unique_url':url,
        'taxcalc_version':taxcalc_version,
        'tables': json.dumps(tables),
        'created_on': created_on,
        'first_year': first_year,
        'is_registered': is_registered,
        'is_behavior': True,
        'microsim_url': microsim_url
    }

    return render(request, 'taxbrain/results.html', context)


