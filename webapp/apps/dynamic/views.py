import json
import datetime
from urlparse import urlparse, parse_qs
import taxcalc

from django.core.mail import send_mail
from django.core import serializers
from django.core.context_processors import csrf
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import loader, Context
from django.template.context import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, TemplateView
from django.contrib.auth.models import User
from django import forms

from djqscsv import render_to_csv_response



tcversion_info = taxcalc._version.get_versions()

taxcalc_version = ".".join([tcversion_info['version'], tcversion_info['full'][:6]])
START_YEARS = ('2013', '2014', '2015')


def dynamic_done(request):
    """
    This view sends an email
    """
    if not request.method=='POST':
        raise Http404

    # Client is giving us the info we need to send email

    email_addr = request.POST['email_address']
    job_id = request.POST['job_id']
    url = "http://www.ospc.org/taxbrain/dynamic/{job}".format(job=job_id)

    send_mail(subject="Your TaxBrain simulation has completed!",
        message = """Hello!

        Good news! Your simulation is done and you can now view the results. Just navigate to
        {url} and have a look!

        Best,
        The TaxBrain Team""".format(url=url),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email_addr])

    response = HttpResponse()

    return response
