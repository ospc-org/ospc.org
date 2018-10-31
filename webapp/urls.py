from django.contrib import admin
from django.conf.urls import include, url

urlpatterns = [

    url(r'^admin/', include(admin.site.urls)),

    url(r'', include("webapp.apps.pages.urls")),
    url(r'^taxbrain/', include("webapp.apps.taxbrain.urls")),
    url(r'^dynamic/', include("webapp.apps.dynamic.urls")),
    url(r'^ccc/', include("webapp.apps.btax.urls")),
    # Third party app urls
    url(r'^account/', include("account.urls")),

    # WHAT DOES THIS DO?
    # static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
]
