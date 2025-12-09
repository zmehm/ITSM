# accounts/apps.py

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # It's good practice to define the default_auto_field as well
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        # Import the signals file to ensure the signal receiver is registered
        import accounts.signals