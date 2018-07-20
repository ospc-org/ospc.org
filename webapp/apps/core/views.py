from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import CoreRun
from .compute import Compute


def process_reform(request):
    fields = dict(request.GET)
    fields.update(dict(request.POST))
    fields = {k: v[0] if isinstance(v, list) else v
              for k, v in list(fields.items())}
    start_year = fields.get('start_year', START_YEAR)
    # TODO: migrate first_year to start_year to get rid of weird stuff like
    # this
    fields['first_year'] = fields['start_year']
    has_errors = make_bool(fields['has_errors'])

    # which file to use, front-end not yet implemented
    data_source = fields.get('data_source', 'PUF')
    use_puf_not_cps = (data_source == 'PUF')

    personal_inputs = TaxBrainForm(start_year, use_puf_not_cps, fields)
    # If an attempt is made to post data we don't accept
    # raise a 400
    if personal_inputs.non_field_errors():
        return BadPost(
            http_response_404=HttpResponse(
                "Bad Input!", status=400
            ),
            has_errors=True
        )
    is_valid = personal_inputs.is_valid()
    if is_valid:
        model = personal_inputs.save(commit=False)
        model.set_fields()
        model.save()
        (reform_dict, assumptions_dict, reform_text, assumptions_text,
            errors_warnings) = model.get_model_specs()

        json_reform = JSONReformTaxCalculator(
            reform_text=json.dumps(reform_dict),
            assumption_text=json.dumps(assumptions_dict),
            raw_reform_text=reform_text,
            raw_assumption_text=assumptions_text,
            errors_warnings_text=json.dumps(errors_warnings)
        )
        json_reform.save()

    user_mods = dict({'policy': reform_dict}, **assumptions_dict)
    data = {'user_mods': user_mods,
            'first_budget_year': int(start_year),
            'use_puf_not_cps': use_puf_not_cps}
    if do_full_calc:
        data_list = [dict(year=i, **data) for i in range(NUM_BUDGET_YEARS)]
        submitted_ids, max_q_length = (
            dropq_compute.submit_dropq_calculation(data_list))
    else:
        data_list = [dict(year=i, **data)
                     for i in range(NUM_BUDGET_YEARS_QUICK)]
        submitted_ids, max_q_length = (
            dropq_compute.submit_dropq_small_calculation(data_list))


def gui_inputs(request):
    """
    Receive data from GUI interface and returns parsed data or default data if
    get request
    """
    start_year = START_YEAR
    has_errors = False
    data_source = DEFAULT_SOURCE
    if request.method == 'POST':
        print('method=POST get', request.GET)
        print('method=POST post', request.POST)
        obj, post_meta = process_reform(request)
        # case where validation failed in forms.TaxBrainForm
        # TODO: assert HttpResponse status is 404
        if isinstance(post_meta, BadPost):
            return post_meta.http_response_404

        # No errors--submit to model
        if not post_meta.stop_submission:
            return redirect(obj)
        # Errors from taxcalc.tbi.reform_warnings_errors
        else:
            personal_inputs = post_meta.personal_inputs
            start_year = post_meta.start_year
            data_source = post_meta.data_source
            use_puf_not_cps = (data_source == 'PUF')
            has_errors = post_meta.has_errors

    else:
        # Probably a GET request, load a default form
        print('method=GET get', request.GET)
        print('method=GET post', request.POST)
        params = parse_qs(urlparse(request.build_absolute_uri()).query)
        if 'start_year' in params and params['start_year'][0] in START_YEARS:
            start_year = params['start_year'][0]

        # use puf by default
        use_puf_not_cps = True
        if ('data_source' in params and
                params['data_source'][0] in DATA_SOURCES):
            data_source = params['data_source'][0]
            if data_source != 'PUF':
                use_puf_not_cps = False

        personal_inputs = TaxBrainForm(first_year=start_year,
                                       use_puf_not_cps=use_puf_not_cps)

    init_context = {
        'form': personal_inputs,
        'params': nested_form_parameters(int(start_year), use_puf_not_cps),
        'taxcalc_version': TAXCALC_VERSION,
        'webapp_version': WEBAPP_VERSION,
        'start_years': START_YEARS,
        'start_year': start_year,
        'has_errors': has_errors,
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
        jobs_to_complete = compute.ready(model.job_ids)
        if jobs_to_complete == 0:
            result = compute.get_result(model.job_ids)
            model.result = result
            model.save()
            return JsonResponse({'eta': 0}, status=202)
        else:
            eta = compute.eta(model.job_ids)
            return JsonResponse({'eta': eta}, status=202)
