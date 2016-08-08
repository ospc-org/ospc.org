from django.conf.urls import patterns, include, url

from .views import btax_results, output_detail, csv_input, csv_output, pdf_view, edit_btax_results


urlpatterns = patterns('',
    url(r'^$', btax_results, name='btax_tax_form'),
    url(r'^(?P<pk>\d+)/output.csv/$', csv_output, name='btax_csv_output'),
    url(r'^(?P<pk>\d+)/input.csv/$', csv_input, name='btax_csv_input'),
    url(r'^(?P<pk>\d+)/', output_detail, name='btax_output_detail'),
    url(r'^pdf/$', pdf_view),
    url(r'^edit/(?P<pk>\d+)/', edit_btax_results, name='btax_edit_btax_results'),
)
