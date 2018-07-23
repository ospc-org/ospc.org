from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from django.utils import timezone
from .models import CoreRun
from ..taxbrain.models import OutputUrl
from .compute import Compute, JobFailError
from ..formatters import get_version
from ..taxbrain.views import TAXCALC_VERSION, WEBAPP_VERSION, dropq_compute
from django.shortcuts import (render, render_to_response, get_object_or_404,
                              redirect)
from django.template.context import RequestContext


def output_detail(request, pk):
    """
    This view is the single page of diplaying a progress bar for how
    close the job is to finishing, and then it will also display the
    job results if the job is done. Finally, it will render a 'job failed'
    page if the job has failed.

    Cases:
        case 1: result is ready and successful

        case 2: model run failed

        case 3: query results
          case 3a: all jobs have completed
          case 3b: not all jobs have completed
    """

    try:
        url = OutputUrl.objects.get(pk=pk)
    except OutputUrl.DoesNotExist:
        raise Http404

    model = url.unique_inputs

    taxcalc_vers_disp = get_version(url, 'taxcalc_vers', TAXCALC_VERSION)
    webapp_vers_disp = get_version(url, 'webapp_vers', WEBAPP_VERSION)

    context_vers_disp = {'taxcalc_version': taxcalc_vers_disp,
                         'webapp_version': webapp_vers_disp}
    if model.tax_result:
        # try to render table; if failure render not available page
        try:
            context = get_result_context(model, request, url)
        except Exception as e:
            print('Exception rendering pk', pk, e)
            traceback.print_exc()
            edit_href = '/taxbrain/edit/{}/?start_year={}'.format(
                pk,
                model.first_year or START_YEAR  # sometimes first_year is None
            )
            not_avail_context = dict(edit_href=edit_href,
                                     **context_vers_disp)
            return render(
                request,
                'taxbrain/not_avail.html',
                not_avail_context)

        context.update(context_vers_disp)
        return render(request, 'taxbrain/results.html', context)
    elif model.error_text:
        return render(request, 'taxbrain/failed.html',
                      {"error_msg": model.error_text.text})
    else:
       job_ids = model.job_ids

        try:
            jobs_ready = dropq_compute.results_ready(job_ids)
        except JobFailError as jfe:
            print(jfe)
            return render_to_response('taxbrain/failed.html')
        print(job_ids)
        if any(j == 'FAIL' for j in jobs_ready):
            failed_jobs = [sub_id for (sub_id, job_ready)
                           in zip(job_ids, jobs_ready)
                           if job_ready == 'FAIL']

            # Just need the error message from one failed job
            error_msgs = dropq_compute.get_results([failed_jobs[0]],
                                                   job_failure=True)
            if error_msgs:
                error_msg = error_msgs[0]
            else:
                error_msg = "Error: stack trace for this error is unavailable"
            val_err_idx = error_msg.rfind("Error")
            error = ErrorMessageTaxCalculator()
            error_contents = error_msg[val_err_idx:].replace(" ", "&nbsp;")
            error.text = error_contents
            error.save()
            model.error_text = error
            model.save()
            return render(request, 'taxbrain/failed.html',
                          {"error_msg": error_contents})

        if all(j == 'YES' for j in jobs_ready):
            results = dropq_compute.get_results(job_ids)
            model.tax_result = results
            model.creation_date = timezone.now()
            model.save()
            context = get_result_context(model, request, url)
            context.update(context_vers_disp)
            return render(request, 'taxbrain/results.html', context)

        else:
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
                context = {'eta': '100'}
                context.update(context_vers_disp)
                return render_to_response(
                    'taxbrain/not_ready.html',
                    context,
                    context_instance=RequestContext(request)
                )


def get_result_context(model, request, url):
    output = model.get_tax_result()
    first_year = model.first_year
    quick_calc = model.quick_calc
    created_on = model.creation_date

    is_from_file = not model.raw_input_fields

    if (model.json_text is not None and (model.json_text.raw_reform_text or
                                         model.json_text.raw_assumption_text)):
        reform_file_contents = model.json_text.raw_reform_text
        reform_file_contents = reform_file_contents.replace(" ", "&nbsp;")
        assump_file_contents = model.json_text.raw_assumption_text
        assump_file_contents = assump_file_contents.replace(" ", "&nbsp;")
    elif model.input_fields is not None:
        reform = to_json_reform(first_year, model.input_fields)
        reform_file_contents = json.dumps(reform, indent=4)
        assump_file_contents = '{}'
    else:
        reform_file_contents = None
        assump_file_contents = None

    is_registered = (hasattr(request, 'user') and
                     request.user.is_authenticated())

    context = {
        'locals': locals(),
        'unique_url': url,
        'created_on': created_on,
        'first_year': first_year,
        'quick_calc': quick_calc,
        'is_registered': is_registered,
        'is_micro': True,
        'reform_file_contents': reform_file_contents,
        'assump_file_contents': assump_file_contents,
        'dynamic_file_contents': None,
        'is_from_file': is_from_file,
        'allow_dyn_links': not is_from_file,
        'results_type': "static"
    }

    if 'renderable' in output:
        context.update({
            'renderable': output['renderable'].values(),
            # 'download_only': output['download_only']
        })

    return context
