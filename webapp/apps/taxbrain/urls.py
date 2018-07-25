from django.conf.urls import url

from .views import (personal_results, csv_input, edit_personal_results,
                    submit_micro, file_input)

from ..core.views import output_detail


urlpatterns = [
    url(r'^$', personal_results, name='tax_form'),
    url(r'^file/$', file_input, name='json_file'),
    url(r'^(?P<pk>\d+)/input.csv/$', csv_input, name='csv_input'),
    url(r'^(?P<pk>[-\d\w]+)/', output_detail, name='output_detail'),
    url(r'^submit/(?P<pk>\d+)/', submit_micro, name='submit_micro'),
    url(r'^edit/(?P<pk>\d+)/', edit_personal_results,
        name='edit_personal_results'),
]
