from django.contrib.auth.models import User
import json
from typing import Type, List

from django.contrib.auth.models import User
from django.contrib.auth.models import User
from django.db import models
from django.http import Http404
from typing import Type, TypeVar, List

from otree_api import call_api

ModelTypeVar = TypeVar('ModelTypeVar')


class BaseModel(models.Model):
    class Meta:
        abstract = True

    # convenience methods with better autocompletion

    @classmethod
    def get(cls: Type[ModelTypeVar], **kwargs) -> ModelTypeVar:
        return cls.objects.filter(**kwargs).get()

    @classmethod
    def get_or_404(cls: Type[ModelTypeVar], **kwargs) -> ModelTypeVar:
        try:
            return cls.get(**kwargs)
        except cls.DoesNotExist as exc:
            msg = f'This {cls.__name__} was not found in the database'
            raise Http404(msg)

    @classmethod
    def filter(cls: Type[ModelTypeVar], **kwargs) -> List[ModelTypeVar]:
        return list(cls.objects.filter(**kwargs))

    def __str__(self):
        return f'{type(self)}:{self.pk}'


class Profile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    aws_access_key_id = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='AWS_ACCESS_KEY_ID'
    )
    aws_secret_access_key = models.CharField(
        max_length=255, blank=True, null=True, verbose_name='AWS_SECRET_ACCESS_KEY'
    )

    def __str__(self):
        return f'{self.user.email}'


class Site(BaseModel):
    url = models.CharField(
        max_length=255,
        verbose_name='URL',
        help_text="For example, http://localhost:8000 or https://myapp.herokuapp.com",
    )
    rest_key = models.CharField(
        max_length=255, verbose_name='OTREE_REST_KEY', blank=True, default=''
    )
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)

    def __str__(self):
        return f'Site:self.url'

    def call_api(self, method, *path_parts, **params) -> dict:
        return call_api(self.url, self.rest_key, method, *path_parts, **params)


class BaseSession(BaseModel):
    class Meta:
        abstract = True
        unique_together = ['site', 'code']

    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='+')
    code = models.CharField(max_length=255)
    config_json = models.TextField(default='')
    session_wide_url = models.CharField(max_length=255)
    admin_url = models.CharField(max_length=255)
    num_participants = models.IntegerField()

    def __str__(self):
        return f'Session:{self.code}'

    @property
    def config(self):
        return json.loads(self.config_json)
