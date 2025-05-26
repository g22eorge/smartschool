from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User

@csrf_exempt
def minimal_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/attendance/minimal-dashboard/')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            # Return JSON response for AJAX or redirect for normal form submission
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully logged in as {username}',
                    'redirect': next_url
                })
            return redirect(next_url)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Invalid credentials'}, status=400)
        return HttpResponse("Invalid credentials", status=400)
    
    # Simple HTML form with CSRF token for testing
    return HttpResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto; padding: 20px; }}
            .form-group {{ margin-bottom: 15px; }}
            label {{ display: block; margin-bottom: 5px; }}
            input[type="text"], input[type="password"] {{ 
                width: 100%; 
                padding: 8px; 
                margin-bottom: 10px;
                box-sizing: border-box;
            }}
            button {{ 
                background: #4CAF50; 
                color: white; 
                padding: 10px 15px; 
                border: none; 
                cursor: pointer; 
            }}
            .error {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Minimal Login</h1>
        <div id="message"></div>
        <form id="loginForm" method="post">
            <input type="hidden" name="next" value="/attendance/minimal-dashboard/">
            <div class="form-group">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username" value="student1" required>
            </div>
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" value="student123" required>
            </div>
            <button type="submit">Login</button>
        </form>
        <p><a href="/attendance/minimal-session/">Check Session</a></p>
        
        <script>
        document.getElementById('loginForm').addEventListener('submit', async function(e) {{
            e.preventDefault();
            
            const formData = new FormData(this);
            const response = await fetch('', {{
                method: 'POST',
                headers: {{
                    'X-Requested-With': 'XMLHttpRequest',
                }},
                body: formData
            }});
            
            const data = await response.json();
            const messageDiv = document.getElementById('message');
            
            if (data.success) {{
                messageDiv.innerHTML = `<div class="success">${{data.message}} Redirecting...</div>`;
                window.location.href = data.redirect;
            }} else {{
                messageDiv.innerHTML = `<div class="error">${{data.message}}</div>`;
            }}
        }});
        </script>
    </body>
    </html>
    """)


@login_required
def minimal_dashboard(request):
    """A simple dashboard that shows user info and session data"""
    user = request.user
    return HttpResponse(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Minimal Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            .user-info {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
            .session-data {{ background: #f0f8ff; padding: 15px; border-radius: 5px; }}
            pre {{ background: #f8f8f8; padding: 10px; border: 1px solid #ddd; border-radius: 3px; overflow-x: auto; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ margin-right: 15px; }}
        </style>
    </head>
    <body>
        <h1>Minimal Dashboard</h1>
        
        <div class="user-info">
            <h2>User Information</h2>
            <p><strong>Username:</strong> {user.username}</p>
            <p><strong>Email:</strong> {user.email or 'N/A'}</p>
            <p><strong>Full Name:</strong> {user.get_full_name() or 'N/A'}</p>
            <p><strong>Is Staff:</strong> {user.is_staff}</p>
            <p><strong>Is Superuser:</strong> {user.is_superuser}</p>
        </div>
        
        <div class="session-data">
            <h2>Session Data</h2>
            <pre>{dict(request.session.items())}</pre>
        </div>
        
        <div class="nav">
            <a href="/attendance/minimal-session/">Check Session</a>
            <a href="/attendance/minimal-logout/">Logout</a>
        </div>
    </body>
    </html>
    """)


def minimal_session(request):
    """View to check session and authentication status"""
    user = request.user
    is_authenticated = user.is_authenticated
    
    response = {
        'is_authenticated': is_authenticated,
        'user': {
            'username': user.username if is_authenticated else None,
            'email': user.email if is_authenticated else None,
        },
        'session': dict(request.session.items()),
        'cookies': request.COOKIES,
    }
    
    return JsonResponse(response)


def minimal_logout(request):
    """Logout the user"""
    auth_logout(request)
    return HttpResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Logged Out</title>
        <meta http-equiv="refresh" content="3;url=/attendance/minimal-login/" />
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .message {{ 
                background: #d4edda; 
                color: #155724; 
                padding: 20px; 
                border-radius: 5px;
                max-width: 500px;
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="message">
            <h2>Successfully logged out</h2>
            <p>You will be redirected to the login page in 3 seconds...</p>
            <p><a href="/attendance/minimal-login/">Click here</a> if you are not redirected.</p>
        </div>
    </body>
    </html>
    """)
