from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from django.forms.models import ModelForm
from . import models


class UserCreationForm(BaseUserCreationForm):
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if '@' not in username:
            raise forms.ValidationError('Username must be an email address')
        return username


class CreateSiteForm(ModelForm):
    class Meta:
        model = models.Site
        fields = ['url', 'rest_key']
