from django.utils import timezone
from django.db import models
from .models import CoreRun
from .compute import Compute, JobFailError
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404, JsonResponse
import itertools
from io import BytesIO
from zipfile import ZipFile
import traceback


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

    def fail(self):
        return render(self.request, 'core/failed.html',
                      {"error_msg": self.object.error_text})

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.outputs:
            try:
                return super().get(self, request, *args, **kwargs)
            except BaseException as e:
                print('Exception rendering pk', pk, e)
                traceback.print_exc()
                return render(request,
                              'core/not_avail.html')
        elif self.object.error_text is not None:
            return self.fail()
        else:
            job_id = str(self.object.job_id)
            try:
                job_ready = self.dropq_compute.results_ready(job_id)
            except JobFailError as jfe:
                self.object.error_text = ""
                self.object.save()
                return self.fail()
            if job_ready == 'FAIL':
                error_msg = self.dropq_compute.get_results(job_id,
                                                           job_failure=True)
                if not error_msg:
                    error_msg = ("Error: stack trace for this error is "
                                 "unavailable")
                val_err_idx = error_msg.rfind("Error")
                error_contents = error_msg[val_err_idx:].replace(" ", "&nbsp;")
                self.object.error_text = error_contents
                self.object.save()
                return self.fail()

            if job_ready == 'YES':
                try:
                    results = self.dropq_compute.get_results(job_id)
                    self.object.outputs = results['outputs']
                    self.object.aggr_outputs = results['aggr_outputs']
                    self.object.creation_date = timezone.now()
                    self.object.save()
                    return super().get(self, request, *args, **kwargs)
                except BaseException as e:
                    print('Exception rendering pk', pk, e)
                    traceback.print_exc()
                    return render(request,
                                  'taxbrain/not_avail.html')
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
                    return render(
                        request,
                        'core/not_ready.html',
                        context
                    )

    def is_from_file(self):
        return not self.object.inputs.raw_gui_field_inputs

    def has_link_to_dyn(self):
        return False


class CoreRunDownloadView(SingleObjectMixin, View):
    model = CoreRun

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        if not self.object.outputs or self.object.error_text:
            return redirect(self.object)

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
