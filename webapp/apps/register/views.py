from django.contrib import auth
from django.template.context_processors import csrf
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, render, redirect
from django.template import RequestContext, Template
from django.template.loader import render_to_string

from django.contrib.auth.models import Permission

from webapp.apps.register.forms import MyRegistrationForm, LoginForm, SubscribeForm
from webapp.apps.register.models import Subscriber

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

    return render(request, 'register/login.html')

def loggedin(request):
    return render_to_response('register/loggedin.html',
        {'full_name': request.user.username})

def invalid_login(request):
    return render_to_response('register/invalid_login.html')

def logout(request):
    auth.logout(request)
    return HttpResponseRedirect(request.META.get('HTTP_REFFER', '/'))

def register_user(request):
    confirm_key = request.GET.get('k')
    subscriber = Subscriber.objects.filter(confirm_key = confirm_key).get()
    if request.method == 'POST':
        form = MyRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            permission = Permission.objects.get(codename = 'view_inputs', content_type__app_label = 'taxbrain')
            form.instance.user_permissions.add(permission)
            return HttpResponseRedirect('/register_success')
        else:
            args = {
                'form': form,
                'username': subscriber.email.split('@')[0] if len(subscriber.email.split('@')[0]) <= 30 else '',
                'email': subscriber.email,
                'confirm_key': confirm_key
            } #Present the user the form with errors to correct.
    else:
        if not confirm_key:
            raise NotImplementedError(
                "We do not handle the case where the user does not have a registration key.")
        elif not Subscriber.objects.filter(confirm_key = confirm_key).exists():
            raise NotImplementedError(
                "We do not handle the case where the user has an incorrect registration key.")
        else:
            subscriber.active = True
            subscriber.save()
            args = {
                'username': subscriber.email.split('@')[0] if len(subscriber.email.split('@')[0]) <= 30 else '',
                'email': subscriber.email,
                'confirm_key': confirm_key
            }

    args.update(csrf(request))
    return render_to_response('register/post-signup-register.html', args)

def register_success(request):
    return render_to_response('register/register_success.html', {},
        context_instance=RequestContext(request))
