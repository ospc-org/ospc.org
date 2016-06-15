from django.conf.urls import patterns, include, url

from views import homepage, aboutpage, newspage, gallerypage
from views import embedpage, widgetpage, newsdetailpage

urlpatterns = patterns('',
    url(r'^$', homepage, name='home'),
    url(r'^about/$', aboutpage, name='about'),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^news/$', newspage, name='news'),
    url(r'^news/news-detail$', newsdetailpage, name='newsdetail'),
    url(r'^widgets/(?P<widget_id>\w+)/$', widgetpage),
    url(r'^widgets/embed/(?P<widget_id>\w+)/$', embedpage),
)
