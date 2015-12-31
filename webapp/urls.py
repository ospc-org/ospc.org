from django.contrib import admin
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.conf.urls.static import static

from webapp.apps.register.views import (
  login,
  logout,
  loggedin,
  invalid_login,
  register_user,
  register_success,
)

urlpatterns = patterns('',

    url(r'^admin/', include(admin.site.urls)),

    url(r'', include("webapp.apps.pages.urls")),
    url(r'^taxbrain/', include("webapp.apps.taxbrain.urls")),
    url(r'^dynamic/', include("webapp.apps.dynamic.urls")),

    # Login & Registration URL Confs
    url(r'^accounts/login/$', login),
    url(r'^logout/$', logout),
    url(r'^loggedin/$', loggedin),
    url(r'^invalid/$', invalid_login),
    url(r'^register/$', register_user, name='register_user'),
    url(r'^register_success/$', register_success),

    # Third party app urls
    url(r'^account/', include("account.urls")),
    url(r'^blog/', include("hermes.urls")),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
