"""
Custom error views for the application.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import requires_csrf_token
from django.template import RequestContext, loader
from django.utils.translation import gettext_lazy as _


@requires_csrf_token
def csrf_failure(request, reason="", template_name='403_csrf.html'):
    """
    Custom CSRF failure view that returns JSON for API requests
    and renders a template for web requests.
    """
    if request.path.startswith('/api/'):
        return JsonResponse(
            {
                'error': 'CSRF verification failed',
                'detail': _('CSRF token missing or incorrect'),
                'status': 403
            },
            status=403
        )
    
    # For web requests, render a template
    from django.conf import settings
    from django.template.loader import render_to_string
    
    context = {
        'title': _('Forbidden (403)'),
        'message': _('CSRF verification failed. Request aborted.'),
        'reason': reason,
        'DEBUG': settings.DEBUG,
    }
    
    return JsonResponse(
        {'error': 'CSRF verification failed'},
        status=403
    )
