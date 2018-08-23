import datetime

from django.utils import timezone
from django.shortcuts import render, redirect
from django.views.generic import View

# Create your views here.
from ..core.models import Tag, TagOption
from ..core.views import CoreRunDetailView, CoreRunDownloadView
from ..core.compute import Compute

from .models import FileInput, FileOutput


class FileInputView(View):
    model = FileInput
    result_header = "Describe"
    template_name = 'fileuploadex/input.html'
    compute = Compute()

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        tmpfile = request.FILES['datafile']
        data_list = [{'data': tmpfile.read(), 'compression': 'gzip'}]
        submitted_id, max_q_length = (
            self.compute.submit_file_upload_test(data_list))
        fi = FileInput()
        fi.save()
        fo = FileOutput()
        fo.inputs = fi
        fo.job_id = submitted_id
        delta = datetime.timedelta(seconds=20)
        fo.exp_comp_datetime = timezone.now() + delta
        fo.save()
        return redirect(fo)


class FileRunDetailView(CoreRunDetailView):
    model = FileOutput

    result_header = "Static Results"

    tags = []
    aggr_tags = [
        Tag(key="default",
            values=[
                TagOption(
                    value="default",
                    title="Descriptive"),
            ])]

    def has_link_to_dyn(self):
        return False


class FileRunDownloadView(CoreRunDownloadView):
    model = FileOutput
