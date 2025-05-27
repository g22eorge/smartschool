from django.urls import path, re_path
from . import views, api
from .views import redirect_to_dashboard
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import RedirectView

app_name = 'dashboard'

urlpatterns = [
    # Redirect root to appropriate dashboard
    path('', redirect_to_dashboard, name='index'),
    path('index/', redirect_to_dashboard, name='dashboard_index'),
    
    # Student dashboard (handle with and without trailing slash)
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/schedule/', views.student_schedule, name='student_schedule'),
    path('student/attendance/', views.student_attendance_records, name='attendance_records'),
    re_path(r'^student$', RedirectView.as_view(url='/dashboard/student/', permanent=True)),
    
    # Lecturer dashboard
    path('lecturer/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/profile/', views.lecturer_profile, name='lecturer_profile'),
    re_path(r'^lecturer$', RedirectView.as_view(url='/dashboard/lecturer/', permanent=True)),
    
    # API Endpoints
    path('api/lecturer/recent-sessions/', api.get_recent_sessions, name='api_recent_sessions'),
    path('api/lecturer/attendance-reports/', api.get_attendance_reports, name='api_attendance_reports'),
    
    # Admin dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    re_path(r'^admin-dashboard$', RedirectView.as_view(url='/dashboard/admin-dashboard/', permanent=True)),
    
    # Legacy URL for backward compatibility
    path('dashboard/', redirect_to_dashboard, name='dashboard'),
    
    # Debug URL
    path('debug/roles/', views.debug_user_roles, name='debug_roles'),
    
    # Attendance reports
    path('attendance-reports/', login_required(views.get_attendance_stats), name='attendance_reports'),
    
    # Attendance submission
    path('submit-attendance/<int:qrcode_id>/', csrf_exempt(views.submit_attendance), name='submit_attendance'),
    
    # Module enrollment
    path('enroll/<int:module_id>/', login_required(views.enroll_in_module), name='enroll_module'),
    
    # Lecturer API endpoints
    path('attendance-stats/', login_required(views.get_attendance_stats), name='attendance_stats'),
    path('schedule/', login_required(views.view_schedule), name='view_schedule'),
    path('module/<int:module_id>/', login_required(views.module_detail), name='module_detail'),
    path('get-active-sessions/', login_required(views.get_active_sessions), name='get_active_sessions'),
    path('api/lecturer/generate-qr/', login_required(views.generate_qr_code), name='generate_qr_code'),
    path('api/lecturer/end-session/<uuid:session_id>/', login_required(views.end_session), name='end_session'),
    path('api/lecturer/active-sessions/', login_required(views.get_active_sessions), name='get_active_sessions'),
    path('api/lecturer/attendance-stats/', login_required(views.get_attendance_stats), name='get_attendance_stats'),
]
