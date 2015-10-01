from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.mail import send_mail
import os
import urllib
from django.core.urlresolvers import reverse

from .models import Subscriber

class SubscribeForm(forms.ModelForm):

  class Meta:
      model = Subscriber
      fields = ('email',)
      widgets = {
          'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder':'Enter email to subscribe'})
      }


class MyRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(MyRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = user.email
        user.is_active = False
        if commit:
          user.save()
          self.send_registration_confirm_email()

        return user

    def confirm_url(self, email):
        hostname = os.environ.get('BASE_IRI', 'http://www.ospc.org')
        return "{host}{path}?{params}".format(
            host = hostname,
            path = '/register_success',
            params = urllib.urlencode({'confirm_email': email})
        )

    def send_registration_confirm_email(self):
      password = self.cleaned_data['password1']
      email = self.cleaned_data['email']
      send_mail(
        subject="Thank you for joining the conversation on American tax policy",
        message = """Welcome!

        Thank you for registering with ospc.org. This is the best way to stay up to date on
        the latest news from the Open Source Policy Center. We also invite you to beta test
        the TaxBrain webapp.

        Email: {email}
        Password: {password}

        Please click here or copy and paste the link in the address bar to complete your registration.
        {url}

        """.format(
            email = email,
            password = password,
            url = self.confirm_url(email)
        ),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email]
      )

class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
