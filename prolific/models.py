import time

from django.contrib.auth.models import User
from django.db import models

from hr.models import BaseModel, BaseSession


class Session(BaseSession):
    completion_url = models.CharField(
        max_length=255,
        null=True,
        verbose_name="Completion URL",
    )
    # currently we don't fill this out anywhere (or even need it)
    # study_id = models.CharField(max_length=255, null=True)


class Worker(BaseModel):

    prolific_pid = models.CharField(max_length=255)
    study_id = models.CharField(max_length=255)

    # sid = "session id" but totally unrelated to oTree Sessions.
    # on prolific it's called 'SESSION_ID'
    prolific_sid = models.CharField(max_length=255, unique=True)

    session: Session = models.ForeignKey(Session, on_delete=models.CASCADE)
