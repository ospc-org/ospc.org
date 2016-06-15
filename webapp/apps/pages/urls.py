from django.conf.urls import patterns, include, url

from views import homepage, aboutpage, newspage, newsdetailpage, widgetpage, gallerypage

urlpatterns = patterns('',
    url(r'^$', homepage, name='home'),
    url(r'^about/$', aboutpage, name='about'),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^news/$', newspage, name='news'),
    url(r'^news/news-detail$', newsdetailpage, name='newsdetail'),
)
