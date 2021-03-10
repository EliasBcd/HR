import time
from typing import TypeVar

from django.contrib.auth.models import User
from django.db import models

from hr.models import BaseModel, BaseSession

ModelTypeVar = TypeVar('ModelTypeVar')


class Session(BaseSession):
    max_assignments = models.IntegerField(null=True)
    use_sandbox = models.BooleanField(null=True)
    expiration = models.FloatField(null=True)
    HITGroupId = models.CharField(default='', max_length=255)
    question_template = models.TextField()

    def worker_url(self):
        # different HITs
        # get the same preview page, because they are lumped into the same
        # "hit group". This is not documented, but it seems HITs are lumped
        # if a certain subset of properties are the same:
        # https://forums.aws.amazon.com/message.jspa?messageID=597622#597622
        # this seems like the correct design; the only case where this will
        # not work is if the HIT was deleted from the server, but in that case,
        # the HIT itself should be canceled.

        # 2018-06-04:
        # the format seems to have changed to this:
        # https://worker.mturk.com/projects/{group_id}/tasks?ref=w_pl_prvw
        # but the old format still works.
        # it seems I can't replace groupId by hitID, which i would like to do
        # because it's more precise.
        subdomain = "workersandbox" if self.use_sandbox else 'www'
        return "https://{}.mturk.com/mturk/preview?groupId={}".format(
            subdomain, self.HITGroupId
        )

    def was_published(self):
        return bool(self.HITGroupId)

    def is_expired(self):
        # self.mturk_expiration is offset-aware, so therefore we must compare
        # it against an offset-aware value.
        return self.expiration and self.expiration < time.time()

    def is_active(self):
        return self.HITGroupId and not self.is_expired()

    def readable_status(self):
        if self.is_active():
            return 'Active'
        if self.is_expired():
            return 'Expired'
        return 'Unpublished'


class HIT(BaseModel):
    hit_id = models.CharField(max_length=255, primary_key=True)
    HITGroupId = models.CharField(max_length=255)
    session: Session = models.ForeignKey(Session, on_delete=models.CASCADE)
    max_assignments = models.IntegerField()


class HITWorker(BaseModel):
    def __str__(self):
        return f'Worker:{self.worker_id}'

    # assignment_id is not unique if 1 worker starts but returns the assignment
    assignment_id = models.CharField(max_length=255)
    worker_id = models.CharField(max_length=255)
    session: Session = models.ForeignKey(Session, on_delete=models.CASCADE)
    # we don't associate it with a HIT because we only receive assignment_id and worker_id
    # from incoming mturk requests
