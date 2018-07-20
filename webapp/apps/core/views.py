from django.shortcuts import render


def get_result_context(model, request, url):
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

    return render('appropriate html page')
