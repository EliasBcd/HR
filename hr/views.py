import html
from django.contrib import messages
import vanilla
from django.contrib.auth import login
from django.http import HttpResponse
from django.shortcuts import redirect, reverse

from otree_api import BaseOTreeApiError
from .forms import UserCreationForm, CreateSiteForm
from .models import Site, Profile


class ExperimenterMixin:
    def dispatch(self, request, *args, **kwargs):
        self.profile = self.request.user.profile
        try:
            return super().dispatch(request, *args, **kwargs)
        except BaseOTreeApiError as exc:
            str_exc = html.escape(str(exc))
            return HttpResponse(
                # the response might be a traceback if the server is in debug mode
                f'The oTree server reported an error: <pre>{str_exc}</pre>'
            )


class Settings(ExperimenterMixin, vanilla.UpdateView):
    template_name = 'hr/Settings.html'
    model = Profile
    fields = ['aws_access_key_id', 'aws_secret_access_key']

    def get_object(self):
        return self.profile

    def get_success_url(self):
        messages.success(self.request, 'Updated profile')
        return reverse('Settings')


class Sites(ExperimenterMixin, vanilla.CreateView):
    template_name = 'hr/Sites.html'
    model = Site
    fields = ['url', 'rest_key']

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs, sites=Site.objects.filter(profile=self.profile)
        )

    def form_valid(self, form):
        site = form.save(commit=False)
        url = site.url.rstrip('/')
        demo_suffix = '/demo'
        if url.endswith(demo_suffix):
            url = url[: -len(demo_suffix)]
        site.url = url
        site.profile = self.profile
        site.save()
        return redirect('Sites')


class Register(vanilla.CreateView):
    template_name = 'hr/Register.html'
    form_class = UserCreationForm

    def form_valid(self, form):
        form.save()
        user = form.instance
        login(self.request, user)
        return redirect('Settings')
