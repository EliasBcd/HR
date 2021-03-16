import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import List

import vanilla
from django import forms
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from hr.models import Site
from hr.views import ExperimenterMixin
from otree_api import GET
from .models import HIT, Session, HITWorker
from .utils import (
    MTurkSettings,
    get_all_assignments,
    get_mturk_client,
    get_completion_code,
    get_worker_ids_by_status,
    MTurkClient,
    in_public_domain,
)
from .forms import CreateHITForm


logger = logging.getLogger(__name__)


class RedirectMTurk(vanilla.View):
    def get(self, request, id):
        session = Session.get_or_404(id=id)

        assignment_id = request.GET['assignmentId']
        worker_id = request.GET['workerId']
        HITWorker.objects.get_or_create(
            assignment_id=assignment_id, worker_id=worker_id, session=session,
        )
        return HttpResponseRedirect(
            session.session_wide_url + '?participant_label=' + worker_id
        )


class MTurkSessions(ExperimenterMixin, vanilla.CreateView):
    template_name = 'mturk/Sessions.html'
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
        if not 'mturk_hit_settings' in config:
            return HttpResponse(
                """mturk_hit_settings not found in the session config"""
            )

        Session.objects.create(
            site=site,
            code=code,
            config_json=json.dumps(config),
            session_wide_url=session_data['session_wide_url'],
            admin_url=session_data['admin_url'],
            num_participants=num_participants,
            question_template=session_data['mturk_template_html'],
        )

        messages.success(request, f'Added session {code}')

        return redirect('MTurkSessions', site_id=site_id)


class SessionMixin:
    def dispatch(self, request, code, *args, **kwargs):
        self.session = Session.get_or_404(code=code)
        return super().dispatch(request, code, *args, **kwargs)


class CreateHIT(ExperimenterMixin, SessionMixin, vanilla.FormView):
    template_name = 'mturk/CreateHIT.html'
    form_class = CreateHITForm

    def dispatch(self, request, *args, **kwargs):
        resp = super().dispatch(request, *args, **kwargs)
        if self.session.was_published():
            return redirect('ManageHIT', code=self.session.code)
        return resp

    def get(self, request, code):

        session = Session.objects.get(code=code)
        config = session.config
        mturk_settings = config['mturk_hit_settings']

        ctx = dict(
            mturk_settings=mturk_settings,
            participation_fee=session.config['participation_fee'],
            session=session,
            num_participants=session.num_participants,
            form=self.form_class(),
        )
        return render(request, 'mturk/CreateHIT.html', ctx)

    def form_valid(self, form: forms.Form):
        request = self.request
        session = Session.get_or_404(code=self.kwargs['code'])

        use_sandbox = form.cleaned_data['use_sandbox']

        if not in_public_domain(request) and not use_sandbox:
            msg = 'oTree must run on a public domain for Mechanical Turk'
            return HttpResponseForbidden(msg)
        mturk_settings = MTurkSettings(**session.config['mturk_hit_settings'])

        start_url = request.build_absolute_uri(
            reverse('RedirectMTurk', args=(session.id,))
        )

        keywords = mturk_settings.keywords
        if isinstance(keywords, (list, tuple)):
            keywords = ', '.join(keywords)

        html_question = render_to_string(
            'mturk/MTurkHTMLQuestion.html',
            context=dict(
                frame_height=mturk_settings.frame_height,
                start_url=start_url,
                question_template=session.question_template,
            ),
        )

        microbatch_size = 9
        num_full_batches, remainder = divmod(
            session.num_participants * 2, microbatch_size
        )
        batch_sizes = [microbatch_size] * num_full_batches
        if remainder > 0:
            batch_sizes.append(remainder)

        with MTurkClient(
            self.profile, use_sandbox=use_sandbox, request=request
        ) as mturk_client:

            for i, batch_size in enumerate(batch_sizes):
                mturk_hit_parameters = {
                    'Title': mturk_settings.title,
                    'Description': mturk_settings.description,
                    'Keywords': keywords,
                    'MaxAssignments': batch_size,
                    'Reward': str(session.config['participation_fee']),
                    'AssignmentDurationInSeconds': 60
                    * mturk_settings.minutes_allotted_per_assignment,
                    'LifetimeInSeconds': int(60 * 60 * mturk_settings.expiration_hours),
                    'UniqueRequestToken': f'otree_{session.code}_{i}',
                    'Question': html_question,
                }

                if not use_sandbox:
                    # drop requirements checks in sandbox mode.
                    mturk_hit_parameters[
                        'QualificationRequirements'
                    ] = mturk_settings.qualification_requirements

                hit = mturk_client.create_hit(**mturk_hit_parameters)['HIT']

                HITGroupId = hit['HITGroupId']
                HIT.objects.create(
                    hit_id=hit['HITId'],
                    HITGroupId=HITGroupId,
                    max_assignments=batch_size,
                    session=session,
                )
            session.use_sandbox = use_sandbox
            session.expiration = hit['Expiration'].timestamp()
            session.HITGroupId = HITGroupId
            session.save()

        return redirect('ManageHIT', session.code)


class ManageHIT(ExperimenterMixin, SessionMixin, vanilla.TemplateView):
    template_name = 'mturk/ManageHIT.html'

    def dispatch(self, request, *args, **kwargs):
        resp = super().dispatch(request, *args, **kwargs)
        if not self.session.was_published():
            return redirect('CreateHIT', code=self.session.code)
        return resp

    def get_context_data(self, **kwargs):
        session = self.session
        return dict(
            is_expired=session.is_expired(),
            is_active=session.is_active(),
            session=session,
        )


class ExpireHIT(ExperimenterMixin, vanilla.View):
    """only POST"""

    def post(self, request, code):
        session = Session.get_or_404(code=code)

        with MTurkClient(
            self.profile, use_sandbox=session.use_sandbox, request=request
        ) as mturk_client:
            expiration = datetime(2015, 1, 1)
            for hit in HIT.filter(session=session):
                mturk_client.update_expiration_for_hit(
                    HITId=hit.hit_id,
                    # If you update it to a time in the past,
                    # the HIT will be immediately expired.
                    ExpireAt=expiration,
                )
            session.expiration = expiration.timestamp()
            session.save()
        # don't need a message because the MTurkCreateHIT page will
        # statically say the HIT has expired.
        return redirect('CreateHIT', code=code)


class MTurkPayments(ExperimenterMixin, SessionMixin, vanilla.TemplateView):
    template_name = 'mturk/MTurkPayments.html'

    def get_context_data(self):
        session = self.session

        assignment_ids_in_db = [
            a.assignment_id for a in HITWorker.filter(session=session)
        ]

        with MTurkClient(
            self.profile, use_sandbox=session.use_sandbox, request=self.request
        ) as mturk_client:
            all_assignments = get_all_assignments(
                mturk_client, [h.hit_id for h in HIT.filter(session=session)]
            )

            # auto-reject participants who submitted without clicking the link,
            # since MTurk will auto-approve them if we don't reject.
            submitted_assignment_ids = [
                a.assignment_id for a in all_assignments if a.status == 'Submitted'
            ]

            auto_rejects = set(submitted_assignment_ids) - set(assignment_ids_in_db)

            for assignment_id in auto_rejects:
                mturk_client.reject_assignment(
                    AssignmentId=assignment_id,
                    RequesterFeedback='Auto-rejecting because this assignment was not found in our database.',
                )

        worker_ids_by_status = get_worker_ids_by_status(all_assignments)

        def filter_workers_by_status(status) -> List[HITWorker]:
            return HITWorker.filter(
                worker_id__in=worker_ids_by_status[status], session=session
            )

        workers_approved = filter_workers_by_status('Approved')
        workers_rejected = filter_workers_by_status('Rejected')
        workers_not_reviewed = filter_workers_by_status('Submitted')

        all_listable_workers = (
            workers_approved + workers_rejected + workers_not_reviewed
        )

        site = session.site
        data = site.call_api(
            GET,
            'session',
            code=session.code,
            participant_labels=[wrk.worker_id for wrk in all_listable_workers],
        )
        from pprint import pprint

        pprint(data)

        participants_list = data['participants']
        participants = {p['label']: p for p in participants_list}
        participation_fee = session.config['participation_fee']
        for lst in [
            workers_not_reviewed,
            workers_approved,
            workers_rejected,
        ]:
            answers = {}
            for assignment in all_assignments:
                answers[assignment.worker_id] = assignment.answer
            for wrk in lst:
                participant = participants[wrk.worker_id]
                # these are not DB properties, just setting it so we can show in template
                wrk.answers_formatted = get_completion_code(answers[wrk.worker_id])
                payoff = participant['payoff_in_real_world_currency']
                wrk.payoff_plus_participation_fee = payoff + participation_fee
                wrk.payoff = payoff
                wrk.finished = participant.get('finished')
                wrk.code = participant['code']

        return dict(
            workers_approved=workers_approved,
            workers_rejected=workers_rejected,
            workers_not_reviewed=workers_not_reviewed,
            participation_fee=participation_fee,
            auto_rejects=auto_rejects,
            session=session,
        )


class PayMTurk(ExperimenterMixin, vanilla.View):
    """only POST"""

    def post(self, request, code):
        session = Session.get_or_404(code=code)
        successful_payments = 0
        failed_payments = 0
        post_data = request.POST
        mturk_client = get_mturk_client(self.profile, use_sandbox=session.use_sandbox)
        payment_page_response = redirect('ManageHIT', code=session.code)

        workers = HITWorker.filter(
            worker_id__in=post_data.getlist('workers'), session=session
        )

        site = session.site
        data = site.call_api(
            GET,
            'session',
            code=session.code,
            participant_labels=[wrk.worker_id for wrk in workers],
        )

        participants_list = data['participants']
        participants = {p['label']: p for p in participants_list}

        for wrk in workers:
            # need the try/except so that we try to pay the rest of the participants

            payoff = participants[wrk.worker_id]['payoff_in_real_world_currency']

            try:
                if payoff > 0:
                    mturk_client.send_bonus(
                        WorkerId=wrk.worker_id,
                        AssignmentId=wrk.assignment_id,
                        BonusAmount='{0:.2f}'.format(Decimal(payoff)),
                        # prevent duplicate payments
                        UniqueRequestToken='{}_{}'.format(wrk.id, wrk.assignment_id),
                        # this field is required.
                        Reason='Thank you',
                    )
                # approve assignment should happen AFTER bonus, so that if bonus fails,
                # the user will still show up in assignments_not_reviewed.
                # worst case is that bonus succeeds but approval fails.
                # in that case, exception will be raised on send_bonus because of UniqueRequestToken.
                # but that's OK, then you can just unselect that participant and pay the others.
                mturk_client.approve_assignment(AssignmentId=wrk.assignment_id)
                successful_payments += 1
            except Exception as e:
                msg = (
                    'Could not pay {} because of an error communicating '
                    'with MTurk: {}'.format(wrk.worker_id, str(e))
                )
                messages.error(request, msg)
                logger.error(msg)
                failed_payments += 1
                if failed_payments > 10:
                    return payment_page_response
        msg = 'Successfully made {} payments.'.format(successful_payments)
        if failed_payments > 0:
            msg += ' {} payments failed.'.format(failed_payments)
            messages.warning(request, msg)
        else:
            messages.success(request, msg)
        return payment_page_response


class RejectMTurk(ExperimenterMixin, vanilla.View):
    """POST only"""

    def post(self, request, code):
        session = Session.get_or_404(code=code)
        post_data = request.POST

        with MTurkClient(
            self.profile, use_sandbox=session.use_sandbox, request=request
        ) as mturk_client:
            for assignment in HITWorker.filter(
                session=session, worker_id__in=post_data.getlist('workers')
            ):
                mturk_client.reject_assignment(
                    AssignmentId=assignment.assignment_id,
                    # The boto3 docs say this param is optional, but if I omit it, I get:
                    # An error occurred (ValidationException) when calling the RejectAssignment operation:
                    # 1 validation error detected: Value null at 'requesterFeedback'
                    # failed to satisfy constraint: Member must not be null
                    RequesterFeedback='',
                )

        messages.success(request, "You successfully rejected " "selected assignments")
        return redirect('ManageHIT', code=code)
