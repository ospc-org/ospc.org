from django.conf.urls import url

from .views import (btax_results, output_detail,
                    edit_btax_results, generate_mock_results)


urlpatterns = [
    url(r'^$', btax_results, name='btax_tax_form'),
    url(r'^(?P<pk>\d+)/', output_detail, name='btax_output_detail'),
    url(r'^edit/(?P<pk>\d+)/', edit_btax_results,
        name='btax_edit_btax_results'),
    url(r'^mock-ccc-results', generate_mock_results,
        name='btax_generate_mock_results')
]
