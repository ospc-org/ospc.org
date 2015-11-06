from django.conf.urls import patterns, include, url

from .views import dynamic_done 

urlpatterns = patterns('',
    url(r'^done$', dynamic_done),
)
