from django.conf.urls import patterns, include, url

from views import (homepage, aboutpage, newspage, gallerypage,
                   embedpage, widgetpage, newsdetailpage,
                   apps_landing_page)


urlpatterns = patterns('',
    url(r'^$', homepage, name='home'), # url(r'^apps/$', apps_landing_page, name='apps'),
    url(r'^about/$', aboutpage, name='about'),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^news/$', newspage, name='news'),
    url(r'^news/news-detail$', newsdetailpage, name='newsdetail'),
    url(r'^gallery/(?P<widget_id>\w+)/$', widgetpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/$', embedpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/(?P<layout>\w+)/$', embedpage),
    url(r'^gallery/$', gallerypage, name='gallery'),
)
