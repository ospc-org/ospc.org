from django.conf.urls import patterns, include, url

from .views import (show_job_submitted, dynamic_input, dynamic_finished,
                    ogusa_results, dynamic_landing, dynamic_behavioral)

urlpatterns = patterns('',
    url(r'^results/(?P<pk>\d+)/', ogusa_results, name='ogusa_results'),
    url(r'^(?P<pk>\d+)/', dynamic_landing, name='dynamic_landing'),
    url(r'^ogusa/(?P<pk>\d+)/', dynamic_input, name='dynamic_input'),
    url(r'^behavioral/(?P<pk>\d+)/', dynamic_behavioral, name='dynamic_input'),
    url(r'^macro/(?P<pk>\d+)/', dynamic_input, name='dynamic_input'),
    url(r'^submitted/(?P<pk>\d+)/', show_job_submitted, name='show_job_submitted'),
    url(r'^dynamic_finished/', dynamic_finished, name='dynamic_finished'),
)
