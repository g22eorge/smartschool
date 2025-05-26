"""
URL configuration for school_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

def root_redirect(request):
    # Debug information
    print("\n=== ROOT REDIRECT ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        print(f"User: {request.user.username}")
        print(f"is_superuser: {request.user.is_superuser}")
        print(f"is_staff: {request.user.is_staff}")
        print(f"is_lecturer: {getattr(request.user, 'is_lecturer', False)}")
        print(f"is_student: {getattr(request.user, 'is_student', False)}")
    print("====================\n")
    
    if not request.user.is_authenticated:
        # For unauthenticated users, redirect to login with next parameter
        next_url = request.GET.get('next', '')
        login_url = reverse('attendance:login')
        if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
            login_url = f"{login_url}?next={next_url}"
        return redirect(login_url)
    
    # For authenticated users, redirect based on role
    if request.user.is_superuser or request.user.is_staff:
        return redirect('dashboard:admin_dashboard')
    elif hasattr(request.user, 'is_lecturer') and request.user.is_lecturer:
        return redirect('dashboard:lecturer_dashboard')
    elif hasattr(request.user, 'is_student') and request.user.is_student:
        return redirect('dashboard:student_dashboard')
    
    # Default fallback
    return redirect('dashboard:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls')),
    path('attendance/', include('attendance.urls')),
    path('core/', include('core.urls')),
    path('', root_redirect, name='root_redirect'),
    path('accounts/login/', RedirectView.as_view(url='/attendance/login/')),  # For admin redirects
    path('accounts/profile/', RedirectView.as_view(url='/')),  # For admin redirects
]

# Serve static and media files in development
if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    
    # Serve static files
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Serve media files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass
