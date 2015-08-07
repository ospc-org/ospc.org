from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.mail import send_mail

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
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super(MyRegistrationForm, self).save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
          user.save()
          self.send_registration_confirm_email()

        return user

    def send_registration_confirm_email(self):
      username = self.cleaned_data['username']
      password = self.cleaned_data['password1']
      email = self.cleaned_data['email']
      send_mail(
        subject="Thank you for joining the conversation on American tax policy",
        message = """Welcome!

        Thank you for registering with ospc.org. This is the best way to stay up to date on
        the latest news from the Open Source Policy Center. We also invite you to beta test
        the TaxBrain webapp.

        Username: {username}
        Password: {password}
        """.format(username=username, password=password),
        from_email = "Open Source Policy Center <mailing@ospc.org>",
        recipient_list = [email]
      )

class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
