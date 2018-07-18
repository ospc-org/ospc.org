from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse

from .models import CoreRun
from .compute import Compute


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
