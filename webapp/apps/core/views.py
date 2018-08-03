import json
from django.utils import timezone
from django.db import models
from .models import CoreRun
from .compute import Compute, JobFailError
from ..formatters import get_version
from ..taxbrain.param_formatters import to_json_reform
from ..taxbrain.models import TaxSaveInputs
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.shortcuts import render_to_response, redirect
from django.http import HttpResponse, Http404, JsonResponse
from django.template.context import RequestContext
import itertools
from io import BytesIO
from zipfile import ZipFile


class SuperclassTemplateNameMixin(object):
    """A mixin that adds the templates corresponding to the core as candidates
    if customized ones aren't found in subclasses."""

    def get_template_names(self):
        names = super().get_template_names()

        # Look for classes that the view inherits from, and that are directly
        # inheriting this mixin
        subclasses = SuperclassTemplateNameMixin.__subclasses__()
        superclasses = self.__class__.__bases__
        classes_to_check = set(subclasses).intersection(set(superclasses))

        for c in classes_to_check:
            # Adapted from
            # https://github.com/django/django/blob/2e06ff8/django/views/generic/detail.py#L142
            if (getattr(c, 'model', None) is not None and
                    issubclass(c.model, models.Model)):
                names.append("%s/%s%s.html" % (
                    c.model._meta.app_label,
                    c.model._meta.model_name,
                    self.template_name_suffix))

        return names


class CoreRunDetailView(SuperclassTemplateNameMixin, DetailView):
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

    model = CoreRun
    dropq_compute = Compute()
    is_editable = True
    result_header = "Results"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.outputs:
            return super().get(self, request, *args, **kwargs)
        elif self.object.error_text:
            return render_to_response(request, 'taxbrain/failed.html',
                                      {"error_msg": self.object.error_text})
        else:
            job_id = str(self.object.job_id)
            try:
                job_ready = self.dropq_compute.results_ready(job_id)
            except JobFailError as jfe:
                return render_to_response('taxbrain/failed.html')
            if job_ready == 'FAIL':
                # Just need the error message from one failed job
                error_msgs = self.dropq_compute.get_results(job_id,
                                                            job_failure=True)
                if not error_msg:
                    error_msg = ("Error: stack trace for this error is "
                                 "unavailable")
                val_err_idx = error_msg.rfind("Error")
                error_contents = error_msg[val_err_idx:].replace(" ", "&nbsp;")
                self.object.error_text = error_contents
                self.object.save()
                return render_to_response(request, 'taxbrain/failed.html',
                                          {"error_msg": error_contents})

            if job_ready == 'YES':
                results = self.dropq_compute.get_results(job_id)
                self.object.outputs = results['outputs']
                self.object.aggr_outputs = results['aggr_outputs']
                self.object.creation_date = timezone.now()
                self.object.save()
                return super().get(self, request, *args, **kwargs)
            else:
                if request.method == 'POST':
                    # if not ready yet, insert number of minutes remaining
                    exp_comp_dt = self.object.exp_comp_datetime
                    utc_now = timezone.now()
                    dt = exp_comp_dt - utc_now
                    exp_num_minutes = dt.total_seconds() / 60.
                    exp_num_minutes = round(exp_num_minutes, 2)
                    exp_num_minutes = (exp_num_minutes if exp_num_minutes > 0
                                       else 0)
                    if exp_num_minutes > 0:
                        return JsonResponse({'eta': exp_num_minutes},
                                            status=202)
                    else:
                        return JsonResponse({'eta': exp_num_minutes},
                                            status=200)

                else:
                    context = {'eta': '100'}
                    return render_to_response(
                        'taxbrain/not_ready.html',
                        context,
                        context_instance=RequestContext(request)
                    )

    def is_from_file(self):
        return not self.object.inputs.raw_input_fields

    def has_link_to_dyn(self):
        return False


class CoreRunDownloadView(SingleObjectMixin, View):
    model = CoreRun

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.outputs or self.object.error_text:
            return redirect(model)

        try:
            downloadables = list(itertools.chain.from_iterable(
                output['downloadable'] for output in self.object.outputs))
        except KeyError:
            raise Http404
        if not downloadables:
            raise Http404

        s = BytesIO()
        z = ZipFile(s, mode='w')
        for i in downloadables:
            z.writestr(i['filename'], i['text'])
        z.close()

        resp = HttpResponse(s.getvalue(), content_type="application/zip")
        resp['Content-Disposition'] = 'attachment; filename={}'.format(
            self.object.zip_filename())
        s.close()
        return resp
