from django.conf.urls import patterns, include, url

from .views import dynamic_submitted, dynamic_input

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/', dynamic_input, name='dynamic_input'),
    url(r'^submitted/(?P<pk>\d+)/', dynamic_submitted, name='dynamic_submitted'),
    #url(r'^results/(?P<pk>\d+)/', dynamic_submitted, name='dynamic_results'),
)
