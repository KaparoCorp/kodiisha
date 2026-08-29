from django.apps import AppConfig


class ArrearsConfig(AppConfig):
    name = 'arrears'

    def ready(self):
        import arrears.signals  # noqa: F401
