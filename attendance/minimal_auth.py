from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def minimal_login(request):
    """A minimal login view that bypasses all middleware and complex logic"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Debug output
        print(f"\n=== MINIMAL LOGIN ===")
        print(f"Username: {username}")
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            print(f"Authentication successful for {user.username}")
            auth_login(request, user)
            print(f"User {user.username} logged in")
            print(f"Is student: {getattr(user, 'is_student', False)}")
            # Redirect to a safe page that doesn't require login
            return redirect('attendance:minimal_home')
        else:
            print("Authentication failed")
            return render(request, 'attendance/minimal_login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'attendance/minimal_login.html')

def minimal_home(request):
    """A minimal home page that shows user info"""
    if not request.user.is_authenticated:
        return redirect('attendance:minimal_login')
    
    user = request.user
    context = {
        'user': {
            'username': user.username,
            'email': user.email,
            'is_student': getattr(user, 'is_student', False),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        },
        'session_key': request.session.session_key,
    }
    return render(request, 'attendance/minimal_home.html', context)

def minimal_logout(request):
    """Log out the user"""
    auth_logout(request)
    return redirect('attendance:minimal_login')
