from django.conf.urls import url

from ..core.views import gui_inputs


urlpatterns = [
    url(r'^$', gui_inputs)
]
