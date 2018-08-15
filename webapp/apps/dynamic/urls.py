from django.conf.urls import url

from .views import (dynamic_landing, dynamic_behavioral,
                    behavior_results, edit_dynamic_behavioral, elastic_results,
                    dynamic_elasticities, edit_dynamic_elastic)


urlpatterns = [
    url(r'^macro/edit/(?P<pk>[-\d\w]+)/', edit_dynamic_elastic,
        name='edit_dynamic_elastic'),
    url(r'^macro/(?P<pk>[-\d\w]+)/', dynamic_elasticities,
        name='dynamic_elasticities'),
    url(r'^macro_results/(?P<pk>[-\d\w]+)/', elastic_results,
        name='elastic_results'),
    url(r'^(?P<pk>[-\d\w]+)/', dynamic_landing, name='dynamic_landing'),
]
