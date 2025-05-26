from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods

@login_required
def help_view(request):
    """Help and support page for users."""
    context = {
        'title': 'Help & Support',
        'is_lecturer': hasattr(request.user, 'is_lecturer') and request.user.is_lecturer,
        'is_student': hasattr(request.user, 'is_student') and request.user.is_student,
        'is_admin': request.user.is_superuser or request.user.is_staff,
    }
    return render(request, 'core/help.html', context)
