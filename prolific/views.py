import json
import logging

import vanilla
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse

from hr.models import Site
from hr.views import ExperimenterMixin
from otree_api import GET, POST
from .models import Session, Worker

logger = logging.getLogger(__name__)


class RedirectProlific(vanilla.View):
    def get(self, request, id):
        session = Session.get_or_404(id=id)

        prolific_pid = request.GET['PROLIFIC_PID']
        prolific_sid = request.GET['SESSION_ID']
        study_id = request.GET['STUDY_ID']
        Worker.objects.get_or_create(
            prolific_pid=prolific_pid,
            study_id=study_id,
            prolific_sid=prolific_sid,
            session=session,
        )
        return HttpResponseRedirect(
            session.session_wide_url + '?participant_label=' + prolific_pid
        )


class ProlificSessions(ExperimenterMixin, vanilla.CreateView):
    template_name = 'prolific/ProlificSessions.html'
    model = Session
    fields = ['code']

    def get_context_data(self, **kwargs):
        site_id = self.kwargs['site_id']
        site = Site.get_or_404(id=site_id)
        sessions = Session.objects.filter(site_id=site_id).order_by('-id')
        return dict(sessions=sessions, site=site)

    def post(self, request, site_id):
        site = get_object_or_404(Site, id=site_id)
        code = request.POST['code']
        session_data = site.call_api(GET, 'session', code=code, participant_labels=[])
        config = session_data['config']
        num_participants = session_data['num_participants']

        Session.objects.create(
            site=site,
            code=code,
            config_json=json.dumps(config),
            session_wide_url=session_data['session_wide_url'],
            admin_url=session_data['admin_url'],
            num_participants=num_participants,
        )

        messages.success(request, f'Added session {code}')

        return redirect('ProlificSessions', site_id=site_id)


class SessionMixin:
    def dispatch(self, request, code, *args, **kwargs):
        self.session = Session.get_or_404(code=code)
        return super().dispatch(request, code, *args, **kwargs)


class ProlificSession(SessionMixin, ExperimenterMixin, vanilla.UpdateView):
    template_name = 'prolific/ProlificSession.html'
    model = Session
    fields = ['completion_url']

    def get_object(self):
        return self.session

    def get_context_data(self, **kwargs):
        session = self.session
        study_url = (
            self.request.build_absolute_uri(
                reverse('RedirectProlific', args=[session.id])
            )
            + '?PROLIFIC_PID={{%PROLIFIC_PID%}}'
            '&STUDY_ID={{%STUDY_ID%}}'
            '&SESSION_ID={{%SESSION_ID%}}'
        )
        example_html = """
        Click <a href="{{ session.prolific_completion_url }}">here</a>
                to complete the study.
        """
        return super().get_context_data(
            study_url=study_url, example_html=example_html, **kwargs
        )

    def form_valid(self, form):
        site = self.session.site

        session = form.save()
        site.call_api(
            POST,
            'session_vars',
            code=session.code,
            vars=dict(prolific_completion_url=session.completion_url),
        )
        messages.success(
            self.request, "Sent your prolific_completion_url to your oTree site"
        )
        return redirect('ProlificSession', session.code)


class ProlificPayments(ExperimenterMixin, SessionMixin, vanilla.TemplateView):
    template_name = 'prolific/ProlificPayments.html'

    def get_context_data(self, **kwargs):
        session = self.session
        site = session.site

        data = site.call_api(GET, 'session', code=session.code)

        unfiltered_participants = data['participants']

        try:
            participants = [
                (pp['label'], pp['payoff_in_real_world_currency'])
                for pp in unfiltered_participants
                if pp['finished'] and pp['payoff_in_real_world_currency'] > 0
            ]
        except KeyError:
            msg = (
                "you need to add 'finished' to PARTICIPANT_FIELDS and " "(oTree 5 only)"
            )
            messages.error(self.request, msg)
            return dict(participants=[], session=session)

        textarea = '\n'.join(f'{tup[0]},{tup[1]}' for tup in participants)

        return dict(participants=participants, session=session, textarea=textarea)
