from django.conf.urls import patterns, include, url

from .views import (
                    # gh pages
                    homepage, aboutpage, portfoliopage, teampage,
                    newsletterpage, newsletter0page, newsletter1page,
                    newsletter2page, newsletter3page, newsletter4page,
                    signuppage, subscribedpage, donatepage,

                    newspage, gallerypage, hellopage,
                    embedpage, widgetpage, newsdetailpage,
                    apps_landing_page, border_adjustment_plot, docspage,
                    gettingstartedpage, subscribed)

urlpatterns = [

    # github pages redirects
    url(r'^$', homepage, name='home'),
    url(r'^about/$', aboutpage, name='about'),
    url(r'^portfolio/$', aboutpage, name='portfolio'),
    url(r'^team/$', teampage, name='team'),
    url(r'^newsletter/$', newsletterpage, name='newsletter'),
    url(r'^newsletter01092019/$', newsletter0page, name='newsletter0'),
    url(r'^newsletter12192018/$', newsletter1page, name='newsletter1'),
    url(r'^newsletter12052018/$', newsletter2page, name='newsletter2'),
    url(r'^newsletter11152018/$', newsletter3page, name='newsletter3'),
    url(r'^newsletter11022018/$', newsletter4page, name='newsletter4'),
    url(r'^signup/$', signuppage, name="signup"),
    url(r'^subscribed/$', subscribedpage, name="subscribed"),
    url(r'^donate/$', donatepage, name="donate"),


    url(r'^getting-started/$', gettingstartedpage, name='gettingstartedpage'),
    url(r'^hello/$', hellopage, name='hello'),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^news/news-detail$', newsdetailpage, name='newsdetail'),
    url(r'^gallery/(?P<widget_id>\w+)/$', widgetpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/$', embedpage),
    url(r'^gallery/embed/(?P<widget_id>\w+)/(?P<layout>\w+)/$', embedpage),
    url(r'^gallery/$', gallerypage, name='gallery'),
    url(r'^docs/$', docspage, name='docs'),
    url(r'^gallery/border_adjustment$', border_adjustment_plot, name='border_adjustment'),
    url(r'^bac/$', border_adjustment_plot, name='border_adjustment')
]
