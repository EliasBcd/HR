from django.contrib import admin
from django.urls import path, include
from django.contrib.auth.decorators import login_required

import hr.views as hr_views
import mturk.views as mturk_views


def _make_path(route, cls, is_experimenter):
    view = cls.as_view()
    if is_experimenter:
        view = login_required(view)
    return path(route, view, name=cls.__name__)


def experimenter_path(route, cls):
    return _make_path(route, cls, is_experimenter=True)


def public_path(route, cls):
    return _make_path(route, cls, is_experimenter=False)


urlpatterns = [
    experimenter_path('', hr_views.Sites),
    public_path('register/', hr_views.Register),
    experimenter_path('profile/', hr_views.Settings),
    public_path('redirect/<code>/', mturk_views.RedirectWorker),
    experimenter_path('sites/<int:site_id>/', mturk_views.Sessions),
    experimenter_path('CreateHIT/<code>/', mturk_views.CreateHIT),
    experimenter_path('SessionPayments/<code>/', mturk_views.SessionPayments),
    experimenter_path('ManageHIT/<code>/', mturk_views.ManageHIT),
    experimenter_path('ExpireHIT/<code>/', mturk_views.ExpireHIT),
    experimenter_path('PayMTurk/<code>/', mturk_views.PayMTurk),
    experimenter_path('RejectMTurk/<code>/', mturk_views.RejectMTurk),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]
