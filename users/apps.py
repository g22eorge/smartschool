from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Users'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This method is called when Django starts.
        This ensures that signal handlers are connected when the application starts.
        """
        # Import signals to connect them
        from . import signals  # noqa
        # Call the ready method from signals if it exists
        if hasattr(signals, 'ready'):
            signals.ready(self)
