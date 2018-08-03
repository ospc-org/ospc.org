from django.conf.urls import url

from .views import (personal_results, csv_input, edit_personal_results,
                    submit_micro, file_input, TaxBrainRunDetailView,
                    TaxBrainRunDownloadView)


urlpatterns = [
    url(r'^$', personal_results, name='tax_form'),
    url(r'^file/$', file_input, name='json_file'),
    url(r'^submit/(?P<pk>[-\d\w]+)/', submit_micro, name='submit_micro'),
    url(r'^edit/(?P<pk>[-\d\w]+)/', edit_personal_results,
        name='edit_personal_results'),
    url(r'^(?P<pk>[-\d\w]+)/input.csv/$', csv_input, name='csv_input'),
    url(r'^(?P<pk>[-\d\w]+)/download/?$', TaxBrainRunDownloadView.as_view(),
        name='download_outputs'),
    url(r'^(?P<pk>[-\d\w]+)/', TaxBrainRunDetailView.as_view(),
        name='output_detail'),
]
