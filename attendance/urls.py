from django.urls import path
from . import views
from .test_views import test_view
from .simple_views import simple_test
from .debug_views import debug_login, check_session
from .test_login import test_login as test_login_view, test_session as test_session_view
from .minimal_login import minimal_login, minimal_dashboard, minimal_session, minimal_logout
from .direct_login import direct_login
from .test_auth import test_login, test_session, test_logout
from .minimal_auth import minimal_login, minimal_home, minimal_logout

app_name = 'attendance'

urlpatterns = [
    path('', views.login_view, name='login'),  # Make login the root URL
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('generate/', views.generate_qr, name='generate_qr'),
    path('generate/<int:module_id>/', views.generate_qr, name='generate_qr_for_module'),
    path('view/<int:qr_id>/', views.view_qr, name='view_qr'),
    path('attendance/<int:module_id>/<int:qr_id>/', views.attendance_detail, name='attendance_detail'),
    path('scan/', views.scan_qr, name='scan_qr'),
    path('deactivate/<int:qr_id>/', views.deactivate_qr, name='deactivate_qr'),
    path('extend/<int:qr_id>/', views.extend_qr_expiration, name='extend_qr'),
    path('qr-history/', views.qr_history_modules, name='qr_history_modules'),
    path('qr-history/<int:module_id>/', views.qr_history, name='qr_history_module'),
    path('student/scan/', views.student_scan, name='student_scan'),
    path('scan/<str:qr_code>/', views.scan_qr_code, name='scan_qr_code'),
    path('attendance/<int:module_id>/', views.attendance_report, name='attendance_report'),
    path('session/<int:qrcode_id>/', views.session_detail, name='session_detail'),
    path('download-attendance/<int:qrcode_id>/', views.download_attendance, name='download_attendance'),
    path('test/', test_view, name='test_view'),
    path('simple/', simple_test, name='simple_test'),
    path('verify-biometric/', views.verify_biometric, name='verify_biometric'),
    # Debug URLs
    path('debug/login/', debug_login, name='debug_login'),
    path('debug/session/', check_session, name='check_session'),
    # Test login URLs (temporary for debugging)
    path('test-login/', test_login, name='test_login'),
    path('test-session/', test_session, name='test_session'),
    # Minimal auth flow (bypasses most middleware)
    path('minimal-login/', minimal_login, name='minimal_login'),
    path('minimal-dashboard/', minimal_dashboard, name='minimal_dashboard'),
    path('minimal-session/', minimal_session, name='minimal_session'),
    path('minimal-logout/', minimal_logout, name='minimal_logout'),
    
    # Direct login (DEBUG only)
    path('direct-login/', direct_login, name='direct_login'),
    
    # Test authentication endpoints
    path('api/test/login/', test_login, name='test_login'),
    path('api/test/session/', test_session, name='test_session'),
    path('api/test/logout/', test_logout, name='test_logout'),
    
    # Minimal authentication flow
    path('minimal/', minimal_login, name='minimal_login'),
    path('minimal/home/', minimal_home, name='minimal_home'),
    path('minimal/logout/', minimal_logout, name='minimal_logout'),
]
