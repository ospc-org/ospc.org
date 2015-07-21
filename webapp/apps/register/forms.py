from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

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

        return user


class LoginForm(AuthenticationForm):
    class Meta:
        fields = ('username', 'password')
