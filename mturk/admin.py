from django.contrib import admin

from .models import *


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'site',
        'num_participants',
        'use_sandbox',
        'expiration',
        'HITGroupId',
    ]


@admin.register(HIT)
class HITAdmin(admin.ModelAdmin):
    list_display = [
        'hit_id',
        'session',
        'HITGroupId',
        'max_assignments',
    ]


@admin.register(HITWorker)
class HITWorkerAdmin(admin.ModelAdmin):
    list_display = ['assignment_id', 'worker_id', 'session']
