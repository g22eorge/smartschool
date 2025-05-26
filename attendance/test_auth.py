from django.http import JsonResponse, HttpResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json

@csrf_exempt
def test_login(request):
    """
    A simple test login endpoint that accepts POST with username and password.
    Returns JSON response with authentication status.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            print(f"\n=== TEST LOGIN ===")
            print(f"Username: {username}")
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                print(f"User authenticated: {user.username}")
                print(f"User is active: {user.is_active}")
                print(f"User is staff: {user.is_staff}")
                print(f"User is superuser: {user.is_superuser}")
                
                # Log the user in
                auth_login(request, user)
                print(f"User logged in. Session key: {request.session.session_key}")
                
                # Get user info
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_authenticated': True,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'session_key': request.session.session_key,
                }
                
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'user': user_info
                })
            else:
                print("Authentication failed - Invalid credentials")
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid username or password'
                }, status=401)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': 'Only POST method is allowed'
    }, status=405)

@login_required
def test_session(request):
    """Test if the user is properly authenticated"""
    return JsonResponse({
        'success': True,
        'message': 'You are authenticated',
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'is_authenticated': request.user.is_authenticated,
            'is_staff': request.user.is_staff,
            'is_superuser': request.user.is_superuser,
        },
        'session': {
            'session_key': request.session.session_key,
            'session_data': dict(request.session)
        }
    })

def test_logout(request):
    """Log out the current user"""
    if request.user.is_authenticated:
        auth_logout(request)
        return JsonResponse({
            'success': True,
            'message': 'Successfully logged out'
        })
    return JsonResponse({
        'success': False,
        'message': 'No user is logged in'
    })
