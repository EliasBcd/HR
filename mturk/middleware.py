import sentry_sdk
from django.http import HttpResponse

from mturk.utils import MTurkError


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, MTurkError):
            sentry_sdk.capture_exception()
            return HttpResponse(repr(exception.__cause__))
