from django.conf.urls import patterns, include, url

from .views import show_job_submitted, dynamic_input, dynamic_finished

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/', dynamic_input, name='dynamic_input'),
    url(r'^submitted/(?P<pk>\d+)/', show_job_submitted, name='show_job_submitted'),
    url(r'^dynamic_finished/', dynamic_finished, name='dynamic_finished'),
    #url(r'^results/(?P<pk>\d+)/', dynamic_submitted, name='dynamic_results'),
)
