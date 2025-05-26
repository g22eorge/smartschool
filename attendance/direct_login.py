from django.http import JsonResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.conf import settings

def direct_login(request):
    """
    Direct login endpoint that accepts username and password as URL parameters.
    Only enabled in DEBUG mode for security.
    """
    if not settings.DEBUG:
        return JsonResponse({
            'success': False,
            'message': 'Direct login is only available in DEBUG mode.'
        }, status=403)

    username = request.GET.get('username')
    password = request.GET.get('password')
    next_url = request.GET.get('next', reverse('dashboard:student_dashboard'))

    if not username or not password:
        return JsonResponse({
            'success': False,
            'message': 'Both username and password are required.',
            'example': f"{request.build_absolute_uri()}?username=student1&password=student123"
        }, status=400)

    # Authenticate user
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        auth_login(request, user)
        return HttpResponseRedirect(next_url)
    else:
        return JsonResponse({
            'success': False,
            'message': 'Invalid credentials.'
        }, status=401)
