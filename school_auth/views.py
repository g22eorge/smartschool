from django.conf import settings
from django.http import JsonResponse

def debug_settings(request):
    """Debug view to show current settings and request info"""
    data = {
        'debug': settings.DEBUG,
        'secure_ssl_redirect': getattr(settings, 'SECURE_SSL_REDIRECT', 'Not set'),
        'secure_proxy_ssl_header': getattr(settings, 'SECURE_PROXY_SSL_HEADER', 'Not set'),
        'secure_hsts_seconds': getattr(settings, 'SECURE_HSTS_SECONDS', 'Not set'),
        'request_is_secure': request.is_secure(),
        'request_meta': {k: str(v) for k, v in request.META.items() if k.startswith('HTTP_') or k in ('CONTENT_TYPE', 'CONTENT_LENGTH')},
    }
    return JsonResponse(data)
