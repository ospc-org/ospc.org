from django.conf.urls import patterns, include, url

from .views import (homepage, aboutpage, newspage, gallerypage, hellopage,
                    embedpage, widgetpage, newsdetailpage, apps_landing_page,
                    border_adjustment_plot, docspage, gettingstartedpage)

urlpatterns = [
    # url(r'^apps/$', apps_landing_page, name='apps'),
    url(r'^$', homepage, name='home'),
    url(r'^about/$', aboutpage, name='about'),
    url(r'^getting-started/$', gettingstartedpage, name='gettingstartedpage'),
    url(r'^hello/$', hellopage, name='hello'),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^news/$', newspage, name='news'),
    url(r'^news/news-detail$', newsdetailpage, name='newsdetail'),
    url(r'^gallery/(?P<widget_id>\w+)/$', widgetpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/$', embedpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/(?P<layout>\w+)/$', embedpage),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^docs/$', docspage, name='docs'),
    url(r'^gallery/border_adjustment$',
        border_adjustment_plot,
        name='border_adjustment'),
    url(r'^bac/$', border_adjustment_plot, name='border_adjustment')
]
