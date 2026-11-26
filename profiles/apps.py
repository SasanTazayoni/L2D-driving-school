from django.apps import AppConfig


class ProfilesConfig(AppConfig):
    """
    This class represents the configuration for the 'profiles' app within
    a Django project. It sets the default auto field to 'BigAutoField' for
    models within the 'profiles' app. Additionally, it imports signals
    module to ensure that signals are registered when the application is
    ready.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'profiles'

    def ready(self):
        # Imported for its side effect: registers the profile signal.
        import profiles.signals  # pylint: disable=import-outside-toplevel,unused-import
