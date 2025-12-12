from django.apps import AppConfig


class LevelsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'levels'
    def ready(self):
        import levels.signals  # or import profiles.signals if it's in the 'profiles' app
