from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.shortcuts import redirect
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def debug_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        logger.info(f"Login attempt - Username: {username}")
        
        user = authenticate(request, username=username, password=password)
        logger.info(f"Authentication result: {user}")
        
        if user is not None:
            auth_login(request, user)
            logger.info(f"User {username} logged in successfully")
            logger.info(f"Session data: {request.session.items()}")
            logger.info(f"User authenticated: {request.user.is_authenticated}")
            
            if user.is_superuser:
                return redirect('dashboard:admin_dashboard')
            elif hasattr(user, 'is_lecturer') and user.is_lecturer:
                return redirect('dashboard:lecturer_dashboard')
            elif hasattr(user, 'is_student') and user.is_student:
                return redirect('dashboard:student_dashboard')
            return redirect('dashboard:index')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'attendance/debug_login.html')

def check_session(request):
    context = {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
        'session_data': dict(request.session.items()),
        'cookies': request.COOKIES,
    }
    return render(request, 'attendance/session_info.html', context)
