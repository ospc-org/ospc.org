from django.conf.urls import url

from .views import (personal_results, csv_input, edit_personal_results,
                    submit_micro, file_input)

from ..core.views import output_detail, download_outputs
from .models import TaxBrainRun


urlpatterns = [
    url(r'^$', personal_results, name='tax_form'),
    url(r'^file/$', file_input, name='json_file'),
    url(r'^submit/(?P<pk>[-\d\w]+)/', submit_micro, name='submit_micro'),
    url(r'^edit/(?P<pk>[-\d\w]+)/', edit_personal_results,
        name='edit_personal_results'),
    url(r'^(?P<pk>[-\d\w]+)/input.csv/$', csv_input, name='csv_input'),
    url(r'^(?P<pk>[-\d\w]+)/download/?$', download_outputs,
        {'model_class': TaxBrainRun}, name='download_outputs'),
    url(r'^(?P<pk>[-\d\w]+)/', output_detail, {'model_class': TaxBrainRun},
        name='output_detail'),
]

download_outputs
