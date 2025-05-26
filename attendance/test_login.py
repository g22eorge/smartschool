from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

@csrf_exempt
def test_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome, {user.username}!')
            
            # Redirect based on user role
            if user.is_superuser:
                return redirect('dashboard:admin_dashboard')
            elif hasattr(user, 'is_lecturer') and user.is_lecturer:
                return redirect('dashboard:lecturer_dashboard')
            elif hasattr(user, 'is_student') and user.is_student:
                return redirect('dashboard:student_dashboard')
            return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'attendance/test_login.html')

def test_session(request):
    return render(request, 'attendance/test_session.html', {
        'user': request.user,
        'is_authenticated': request.user.is_authenticated,
        'session': dict(request.session.items()),
        'cookies': request.COOKIES,
    })
