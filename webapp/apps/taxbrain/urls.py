from django.conf.urls import patterns, include, url

from .views import (personal_results, output_detail, csv_input, csv_output, pdf_view, edit_personal_results, submit_micro, json_input)



urlpatterns = patterns('',
    url(r'^$', personal_results, name='tax_form'),
    url(r'^json/$', json_input, name='json_form'),
    url(r'^(?P<pk>\d+)/output.csv/$', csv_output, name='csv_output'),
    url(r'^(?P<pk>\d+)/input.csv/$', csv_input, name='csv_input'),
    url(r'^(?P<pk>\d+)/', output_detail, name='output_detail'),
    url(r'^submit/(?P<pk>\d+)/', submit_micro, name='submit_micro'),
    url(r'^pdf/$', pdf_view),
    url(r'^edit/(?P<pk>\d+)/', edit_personal_results, name='edit_personal_results'),
)
