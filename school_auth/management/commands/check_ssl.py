from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Check SSL settings'

    def handle(self, *args, **options):
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"SECURE_SSL_REDIRECT: {getattr(settings, 'SECURE_SSL_REDIRECT', 'Not set')}")
        self.stdout.write(f"SECURE_PROXY_SSL_HEADER: {getattr(settings, 'SECURE_PROXY_SSL_HEADER', 'Not set')}")
        self.stdout.write(f"SECURE_HSTS_SECONDS: {getattr(settings, 'SECURE_HSTS_SECONDS', 'Not set')}")
        self.stdout.write(f"Request.is_secure() would return: {settings.SECURE_PROXY_SSL_HEADER is not None}")
