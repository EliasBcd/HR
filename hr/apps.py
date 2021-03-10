from django.apps import AppConfig



class HrConfig(AppConfig):
    name = 'hr'

    def ready(self):
        # make the signals register
        from . import signals  # noqa
