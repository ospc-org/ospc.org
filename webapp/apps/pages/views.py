from django.http import Http404
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.views.generic import TemplateView, DetailView
from webapp.apps.register.forms import SubscribeForm
from django.core.context_processors import csrf
from django.conf import settings
import os

BLOG_URL = os.environ.get('BLOG_URL', 'www.ospc.org')

def settings_context_processor(request):
    return {'BLOG_URL': settings.BLOG_URL}

def subscribeform(request):
    if request.method == 'POST':
        subscribeform = SubscribeForm(request.POST)
        if subscribeform.is_valid():
            subscriber = subscribeform.save()
            subscriber.send_subscribe_confirm_email()
    else:
        subscribeform = SubscribeForm()
    return subscribeform

def check_email(request):
    return render(request, 'register/please-check-email.html', {})

def homepage(request):
    form = subscribeform(request)
    csrf_token = csrf(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)
    test = render(request, 'pages/home_content.html', {
        'csrv_token': csrf(request)['csrf_token'],
        'email_form': form,
        'section': {
            'active_nav': 'home',
            'title': 'Welcome to the Open Source Policy Center',
        },
        'username': request.user
    })

    return test

def aboutpage(request):
    form = subscribeform(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)
    test_1 = render(request, 'pages/about.html', {
        'csrv_token': csrf(request)['csrf_token'],
        'email_form': form,
        'section': {
            'active_nav': 'about',
            'title': 'About',
        }
    })
    return test_1

def newspage(request):
    return redirect(BLOG_URL)

def newsdetailpage(request):
    return redirect(BLOG_URL)

def _discover_widgets():
    '''stubbed out data I wish to recieve from some widget discovery mechanism'''
    tre_widget = dict()
    tre_widget['title'] = 'Tax Reform Explorer'
    tre_widget['src'] = 'http://bcollins-outbox.s3.amazonaws.com/tax-reform-explorer.html'
    tre_widget['include_email'] = True

    widgets = dict()
    widgets['taxreformexplorer'] = tre_widget

    return widgets

def widgetpage(request, widget_id):

    widgets = _discover_widgets()

    if widget_id not in widgets.keys():
        raise ValueError('Invalid Widget Id {0}'.format(widget_id))

    widget = widgets[widget_id]

    form = subscribeform(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)

    test_1 = render(request, 'pages/widget.html', {
        'csrv_token': csrf(request)['csrf_token'],
        'email_form': form,
        'widget_title': widget['title'],
        'widget_url': widget['src'],
        'section': {
            'title': 'Widget',
        }
    })
    return test_1
