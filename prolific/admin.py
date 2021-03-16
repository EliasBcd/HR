from django.contrib import admin

from .models import *


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'site',
        #'study_id',
        'num_participants',
    ]


@admin.register(Worker)
class HITWorkerAdmin(admin.ModelAdmin):
    list_display = ['prolific_pid', 'study_id', 'session']
