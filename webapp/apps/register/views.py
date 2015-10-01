from django.contrib import auth
from django.core.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render, redirect
from django.template import RequestContext, Template
from django.template.loader import render_to_string

from django.contrib.auth.models import Permission

from webapp.apps.register.forms import MyRegistrationForm, LoginForm, SubscribeForm
from webapp.apps.register.models import Subscriber
from django.contrib.auth.models import User
import urllib

def login(request):
    redirect_to = request.REQUEST.get('next', '/')

    if request.method=='POST':
        log_user = LoginForm(request.POST)

        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect(redirect_to)
        else:
            error_msg = "The username and/or password are incorrect."
            error_context = {'error_msg': error_msg, 'log_user': log_user}
            return render(request, 'register/login.html', error_context)

    else:
        log_user = LoginForm()

    log_context = {'log_user': log_user}

    return render(request, 'register/login.html', log_context)

def loggedin(request):
    return render_to_response('register/loggedin.html',
        {'full_name': request.user.username})

def invalid_login(request):
    return render_to_response('register/invalid_login.html')

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFFER', '/'))

def register_user(request):
    if request.method == 'POST':
        form = MyRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            permission = Permission.objects.get(codename = 'view_inputs', content_type__app_label = 'taxbrain')
            form.instance.user_permissions.add(permission)
            return render_to_response('register/confirm_registration.html')
        else:
            args = {'form': form} #Present the user the form with errors to correct.
    else:
        confirm_key = request.GET.get('k')
        if confirm_key and Subscriber.objects.filter(confirm_key = confirm_key).exists():
            subscriber = Subscriber.objects.filter(confirm_key = confirm_key).get()
            subscriber.active = True
            subscriber.save()
            return render_to_response('register/subscribe_success.html')

        args = {}
        args['form'] = MyRegistrationForm()
        args.update(csrf(request))
        return render_to_response('register/register.html', args)

def register_success(request):
    confirm_email = request.GET.get('confirm_email')
    if confirm_email and User.objects.filter(email = urllib.unquote(confirm_email)).exists():
        user = User.objects.filter(email = urllib.unquote(confirm_email)).get()
        user.is_active = True
        user.save()
        return render_to_response('register/register_success.html')
    return HttpResponseRedirect('/')
