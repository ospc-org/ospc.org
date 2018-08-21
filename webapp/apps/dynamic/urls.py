from django.conf.urls import url

from .views import (dynamic_landing,
                    dynamic_elasticities, edit_dynamic_elastic,
                    TaxBrainElastRunDetailView, TaxBrainElastRunDownloadView)


urlpatterns = [
    url(r'^macro/edit/(?P<pk>[-\d\w]+)/', edit_dynamic_elastic,
        name='edit_dynamic_elastic'),
    url(r'^macro/(?P<pk>[-\d\w]+)/', dynamic_elasticities,
        name='dynamic_elasticities'),
    url(r'^macro/(?P<pk>[-\d\w]+)/download/?$', TaxBrainElastRunDownloadView.as_view(),
        name='elast_download_outputs'),
    url(r'^macro_results/(?P<pk>[-\d\w]+)/', TaxBrainElastRunDetailView.as_view(),
        name='elast_output_detail'),
    url(r'^(?P<pk>[-\d\w]+)/', dynamic_landing, name='dynamic_landing'),
]
