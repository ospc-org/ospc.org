
import os

from django.http import Http404
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.views.generic import TemplateView, DetailView
from webapp.apps.register.forms import SubscribeForm
from django.core.context_processors import csrf
from django.conf import settings

import requests

BLOG_URL = os.environ.get('BLOG_URL', 'www.ospc.org')
EMAIL_DEFAULT = '1'

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

def gallerypage(request):
    return render(request, 'pages/gallery.html', {
        'manifest_url': os.environ.get('TAXPLOT_MANIFEST_URL')
    })

def newspage(request):
    return redirect(BLOG_URL)

def newsdetailpage(request):
    return redirect(BLOG_URL)


def _discover_widgets():
    '''stubbed out data I wish to recieve from some widget discovery mechanism'''

    manifest_url = os.environ.get('TAXPLOT_MANIFEST_URL')

    if not manifest_url:
        raise ValueError('TAXPLOT_MANIFEST_URL environment variable not set')

    resp = requests.get(manifest_url)
    resp.raise_for_status()

    widgets = resp.json()
    return { w['plot_id'] : w for w in widgets }

def widgetpage(request, widget_id):

    widgets = _discover_widgets()

    if widget_id not in widgets.keys():
        raise ValueError('Invalid Widget Id {0}'.format(widget_id))

    widget = widgets[widget_id]

    form = subscribeform(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)

    request.get_host()
    embed_url = os.path.join('http://',request.get_host(), 'gallery', 'embed', widget_id)

    if request.method == 'GET':
        include_email = request.GET.get('includeEmail', EMAIL_DEFAULT) == '1'
    else:
        include_email = False

    return render(request, 'pages/widget.html', {
        'csrv_token': csrf(request)['csrf_token'],
        'email_form': form,
        'embed_url': embed_url,
        'include_email': include_email,
        'best_width': widget.get('best_width'),
        'best_height': widget.get('best_height'),
        'widget_title': widget['plot_name'],
        'widget_url': widget['plot_url'],
        'long_description': widget['long_description'],
        'Concept_credit': widget['Concept_credit'],
        'Development_credit': widget['Development_credit'],
        'OSS_credit': widget['OSS_credit'],
        'section': {
            'title': 'Widget',
        }
    })

def embedpage(request, widget_id):
    form = subscribeform(request)

    widgets = _discover_widgets()

    if widget_id not in widgets.keys():
        raise ValueError('Invalid Widget Id {0}'.format(widget_id))

    widget = widgets[widget_id]

    form = subscribeform(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)

    if request.method == 'GET':
        include_email = request.GET.get('includeEmail', '') == '1'
    else:
        include_email = False

    return render(request, 'pages/embed.html', {
        'best_width': widget.get('best_width'),
        'best_height': widget.get('best_height'),
        'widget_title': widget['plot_name'],
        'widget_url': widget['plot_url'],
        'email_form': form,
        'include_email': include_email,
    })
