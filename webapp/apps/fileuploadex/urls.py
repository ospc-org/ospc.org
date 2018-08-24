

from django.conf.urls import url

from .views import (FileInputView, FileRunDetailView, FileRunDownloadView)


urlpatterns = [
    url(r'^$', FileInputView.as_view(),
        name='fileinput'),
    url(r'^(?P<pk>[-\d\w]+)/download/?$', FileRunDetailView.as_view(),
        name='file_results'),
    url(r'^(?P<pk>[-\d\w]+)/', FileRunDownloadView.as_view(),
        name='fileinput_download')
]
