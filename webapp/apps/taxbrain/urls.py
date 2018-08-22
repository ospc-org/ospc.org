from django.conf.urls import url

from .views import (personal_results, edit_personal_results,
                    resubmit, file_input, TaxBrainRunDetailView,
                    TaxBrainRunDownloadView)


urlpatterns = [
    url(r'^$', personal_results, name='tax_form'),
    url(r'^file/$', file_input, name='json_file'),
    url(r'^submit/(?P<pk>[-\d\w]+)/', resubmit, name='resubmit'),
    url(r'^edit/(?P<pk>[-\d\w]+)/', edit_personal_results,
        name='edit_personal_results'),
    url(r'^(?P<pk>[-\d\w]+)/download/?$', TaxBrainRunDownloadView.as_view(),
        name='download_outputs'),
    url(r'^(?P<pk>[-\d\w]+)/', TaxBrainRunDetailView.as_view(),
        name='output_detail'),
]
