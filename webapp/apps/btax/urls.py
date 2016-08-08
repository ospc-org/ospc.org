from django.conf.urls import patterns, include, url

from .views import btax_results, output_detail, csv_input, csv_output, pdf_view, edit_btax_results


urlpatterns = patterns('',
    url(r'^$', btax_results, name='tax_form'),
    url(r'^(?P<pk>\d+)/output.csv/$', csv_output, name='csv_output'),
    url(r'^(?P<pk>\d+)/input.csv/$', csv_input, name='csv_input'),
    url(r'^(?P<pk>\d+)/', output_detail, name='output_detail'),
    url(r'^pdf/$', pdf_view),
    url(r'^edit/(?P<pk>\d+)/', edit_btax_results, name='edit_btax_results'),
)
