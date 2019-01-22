
import os

from django.http import Http404
from django.shortcuts import render, render_to_response, redirect
from django.template import RequestContext
from django.views.generic import TemplateView, DetailView
from webapp.apps.register.forms import SubscribeForm
from django.template.context_processors import csrf
from django.conf import settings
from django.views.decorators.clickjacking import xframe_options_exempt

import requests

import btax
import taxcalc

BTAX_VERSION = btax.__version__
TAXCALC_VERSION = taxcalc.__version__

BLOG_URL = os.environ.get('BLOG_URL', 'www.ospc.org')
GH_PAGES_URL = "https://ospc-org.github.io"
EMAIL_DEFAULT = '1'

# GH Pages redirect views:
# https://ospc-org.github.io/#about
# https://ospc-org.github.io/portfolio/
# https://ospc-org.github.io/team/
# https://ospc-org.github.io/newsletter/
# https://ospc-org.github.io/newsletter01092019/
# https://ospc-org.github.io/newsletter12192018/
# https://ospc-org.github.io/newsletter12052018/
# https://ospc-org.github.io/newsletter11152018/
# https://ospc-org.github.io/newsletter11022018/
# https://ospc-org.github.io/signup/
# https://ospc-org.github.io/subscribed/
# https://ospc-org.github.io/donate/


def homepage(request):
    return redirect(GH_PAGES_URL)

def aboutpage(request):
    return redirect(GH_PAGES_URL + "/#about")

def teampage(request):
    return redirect(GH_PAGES_URL + "/team/")

def portfoliopage(request):
    return redirect(GH_PAGES_URL + "/portfolio/")

def newsletterpage(request):
    return redirect(GH_PAGES_URL + "/newsletter/")

def newsletter0page(request):
    return redirect(GH_PAGES_URL + "/newsletter01092019/")

def newsletter1page(request):
    return redirect(GH_PAGES_URL + "/newsletter12192018/")

def newsletter2page(request):
    return redirect(GH_PAGES_URL + "/newsletter12052018/")

def newsletter3page(request):
    return redirect(GH_PAGES_URL + "/newsletter11152018/")

def newsletter4page(request):
    return redirect(GH_PAGES_URL + "/newsletter11022018/")

### add next newsletter here


def signuppage(request):
    return redirect(GH_PAGES_URL + "/signup/")

def subscribedpage(request):
    return redirect(GH_PAGES_URL + "/subscribed/")

def donatepage(request):
    return redirect(GH_PAGES_URL + "/donate/")


#### end redirect views

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


def subscribed(request):
    return render(request, 'pages/thanks-for-subscribing.html')


def check_email(request):
    return render(request, 'register/please-check-email.html', {})

def gallerypage(request):
    return render(request, 'pages/gallery.html', {
        'manifest_url': os.environ.get('TAXPLOT_MANIFEST_URL'),
        'section': {
            'active_nav': 'gallery',
            'title': 'Open Source Policy Center Gallery',
        },
    })

def hellopage(request):
    return render(request, 'pages/hello.html', {
        'manifest_url': os.environ.get('TAXPLOT_MANIFEST_URL'),
        'section': {
            'active_nav': 'hello',
            'title': 'Hello',
        },
    })

def newspage(request):
    return redirect(BLOG_URL)

def newsdetailpage(request):
    return redirect(BLOG_URL)

def docspage(request):
    return render(request, 'pages/docs.html', {
        'section': {
            'active_nav': 'docs',
            'title': 'Open Source Policy Center Documentation',
        },
    })

def gettingstartedpage(request):
    return render(request, 'pages/gettingstarted.html', {
        'section': {
            'active_nav': 'getting-started',
            'title': 'Getting Started',
        },
    })

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

    if widget_id not in list(widgets.keys()):
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
        'best_width_portrait': widget.get('best_width_portrait'),
        'best_height_portrait': widget.get('best_height_portrait'),
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

def border_adjustment_plot(request):
    return render(request, 'pages/border_adjustment.html', {
        'section': {
            'title': 'Widget',
        }
    })

@xframe_options_exempt
def embedpage(request, widget_id, layout='landscape'):
    form = subscribeform(request)

    widgets = _discover_widgets()

    if widget_id not in list(widgets.keys()):
        raise ValueError('Invalid Widget Id {0}'.format(widget_id))

    widget = widgets[widget_id]

    form = subscribeform(request)
    if request.method == 'POST' and form.is_valid():
        return check_email(request)

    if request.method == 'GET':
        include_email = request.GET.get('includeEmail', '') == '1'
    else:
        include_email = False

    gallery_link = os.path.join('http://',request.get_host(), 'gallery', widget_id)
    if layout == 'portrait':
        response_obj = {
	    'best_width': widget.get('best_width_portrait'),
	    'best_height': widget.get('best_height_portrait'),
	    'widget_title': widget['plot_name'],
	    'widget_url': widget['plot_url'].replace('landscape','portrait'),
	    'email_form': form,
	    'include_email': include_email,
	    'long_description': widget['long_description'],
	    'Concept_credit': widget['Concept_credit'],
	    'Development_credit': widget['Development_credit'],
	    'OSS_credit': widget['OSS_credit'],
	    'gallery_link': gallery_link,
        }
    else:
        response_obj = {
	    'best_width': widget.get('best_width'),
	    'best_height': widget.get('best_height'),
	    'widget_title': widget['plot_name'],
	    'widget_url': widget['plot_url'],
	    'email_form': form,
	    'include_email': include_email,
	    'long_description': widget['long_description'],
	    'Concept_credit': widget['Concept_credit'],
	    'Development_credit': widget['Development_credit'],
	    'OSS_credit': widget['OSS_credit'],
	    'gallery_link': gallery_link,
        }

    return render(request, 'pages/embed.html', response_obj)

def apps_landing_page(request):
    context = {'btax_version': BTAX_VERSION,
               'taxcalc_version': TAXCALC_VERSION,
              }
    return render(request, 'pages/apps.html', context)
