from django.conf.urls import patterns, include, url

from .views import (show_job_submitted, dynamic_input, dynamic_finished,
                    ogusa_results, dynamic_landing, dynamic_behavioral,
                    behavior_results, edit_dynamic_behavioral,
                    dynamic_elasticities, elastic_results, elastic_output,
                    edit_dynamic_elastic)

urlpatterns = patterns('',
    url(r'^results/(?P<pk>\d+)/', ogusa_results, name='ogusa_results'),
    url(r'^(?P<pk>\d+)/', dynamic_landing, name='dynamic_landing'),
    url(r'^ogusa/(?P<pk>\d+)/', dynamic_input, name='dynamic_input'),
    url(r'^behavioral/(?P<pk>\d+)/', dynamic_behavioral, name='dynamic_behavioral'),
    url(r'^behavioral/edit/(?P<pk>\d+)/', edit_dynamic_behavioral, name='edit_dynamic_behavioral'),
    url(r'^macro/edit/(?P<pk>\d+)/', edit_dynamic_elastic, name='edit_dynamic_elastic'),
    url(r'^macro/(?P<pk>\d+)/', dynamic_elasticities, name='dynamic_elasticities'),
    url(r'^submitted/(?P<pk>\d+)/', show_job_submitted, name='show_job_submitted'),
    url(r'^macro_processing/(?P<pk>\d+)/', elastic_results, name='elastic_results'),
    url(r'^macro_results/(?P<pk>\d+)/', elastic_output, name='elastic_output'),
    url(r'^behavior_results/(?P<pk>\d+)/', behavior_results, name='behavior_results'),
    url(r'^dynamic_finished/', dynamic_finished, name='dynamic_finished'),
)
