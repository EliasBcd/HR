from django.contrib import admin

# Register your models here.
from hr.models import Site, Profile


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = [
        'url',
        'profile',
    ]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user']
