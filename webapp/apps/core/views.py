import json
from collections import namedtuple

from django.shortcuts import render, get_object_or_404
from django.http import (HttpResponse, JsonResponse)

from ..taxbrain.forms import TaxBrainForm as Form
from ..taxbrain.param_displayers import nested_form_parameters
from ..constants import START_YEAR, START_YEARS, DATA_SOURCES, DEFAULT_SOURCE

from .models import CoreRun
from .compute import Compute, NUM_BUDGET_YEARS, NUM_BUDGET_YEARS_QUICK

import taxcalc
from django.conf import settings


WEBAPP_VERSION = settings.WEBAPP_VERSION

tcversion_info = taxcalc._version.get_versions()

TAXCALC_VERSION = tcversion_info['version']


PostMeta = namedtuple(
    'PostMeta',
    ['form', 'start_year', 'data_source']
)

BadPost = namedtuple(
    'BasdPost',
    ['http_response_404', 'has_errors']
)


def process_reform(request):
    fields = dict(request.GET)
    fields.update(dict(request.POST))
    fields = {k: v[0] if isinstance(v, list) else v
              for k, v in list(fields.items())}
    start_year = fields.get('start_year', START_YEAR)
    # TODO: migrate first_year to start_year to get rid of weird stuff like
    # this
    fields['first_year'] = fields['start_year']

    data_source = fields.get('data_source', 'PUF')
    use_puf_not_cps = (data_source == 'PUF')

    # TODO: figure out correct way to grab quick_calc flag
    do_full_calc = False if fields.get('quick_calc') else True

    form = Form(start_year, use_puf_not_cps, fields)
    # If an attempt is made to post data we don't accept
    # raise a 400
    if form.non_field_errors():
        return BadPost(
            http_response_404=HttpResponse(
                "Bad Input!", status=400
            ),
            has_errors=True
        )
    is_valid = form.is_valid()
    if is_valid:
        model = form.save(commit=False)
        model.set_fields()
        model.save()
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = model.get_model_specs()
        # TODO: save processed data

    user_mods = dict({'policy': reform_dict}, **assumptions_dict)
    data = {'user_mods': user_mods,
            'first_budget_year': int(start_year),
            'use_puf_not_cps': use_puf_not_cps}
    compute = Compute()
    if do_full_calc:
        data_list = [dict(year=i, **data) for i in range(NUM_BUDGET_YEARS)]
        submitted_ids, max_q_length = (
            compute.submit_calculation_job(data_list))
    else:
        data_list = [dict(year=i, **data)
                     for i in range(NUM_BUDGET_YEARS_QUICK)]
        submitted_ids, max_q_length = (
            compute.submit_small_calculation_job(data_list))

    return unique_url, PostMeta(
        form=form,
        start_year=start_year,
        data_source=data_source
    )


def gui_inputs(request):
    """
    Receive data from GUI interface and returns parsed data or default data if
    get request
    """
    start_year = START_YEAR
    data_source = DEFAULT_SOURCE
    if request.method == 'POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        obj, post_meta = process_reform(request)
        if isinstance(post_meta, BadPost):
            return post_meta.http_response_404
        form = post_meta.form
        start_year = post_meta.start_year
        data_source = post_meta.data_source
        use_puf_not_cps = (data_source == 'PUF')
        if not post_meta.stop_submission:
            return redirect(obj)

    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        start_year = request.GET.get('start_year', START_YEAR)
        data_source = request.GET.get('data_source', DEFAULT_SOURCE)
        use_puf_not_cps = (data_source == 'PUF')
        form = Form(first_year=start_year,
                    use_puf_not_cps=use_puf_not_cps)

    init_context = {
        'form': form,
        'params': nested_form_parameters(int(start_year), use_puf_not_cps),
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'data_sources': DATA_SOURCES,
        'data_source': data_source,
    }

    return render(request, 'taxbrain/input_form.html', init_context)



def get_result_context(request, model, url):
    """
    generate context from request object and model and url model objects

    returns: context
    """

    context = {
        # ...
    }
    return context


def outputs(request, id):
    """
    Query status of jobs, render result upon completion of all jobs

    Cases:
        case 1: result is ready and successful

        case 2: model run failed

        case 3: query results
          case 3a: all jobs have completed
          case 3b: not all jobs have completed

    returns: data to be rendered and displayed
    """

    model = get_object_or_404(CoreRun, id=id)

    compute = Compute()

    if model.result is not None:
        context = get_result_context(request, model)
        return render('outputs.html', context)
    elif model.error_message is not None:
        context = {'error': model.error_message}
        return render('failed.html', context)
    else:
        jobs_ready = compute.results_ready(model.job_ids)
        if jobs_ready == model.job_ids:
            result = compute.get_results(model.job_ids)
            model.result = result
            model.save()
            return JsonResponse({'eta': 0}, status=202)
        else:
            eta = compute.eta(model.job_ids)
            return JsonResponse({'eta': eta}, status=202)
