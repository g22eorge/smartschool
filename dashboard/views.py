from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib import messages
from django.utils import timezone
from django.db.models import Prefetch
from django.http import Http404
from attendance.models import Module, QRCode, Attendance
from datetime import timedelta, datetime, time as time_type
from attendance.models import Attendance, QRCode, Module
from .models import ClassSchedule
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import qrcode
import qrcode.image.svg
from io import BytesIO
import uuid
from datetime import timedelta
from django.db.models import Count, F, Q, ExpressionWrapper, FloatField
from django.urls import resolve

User = get_user_model()
from attendance.models import Module, QRCode, Attendance
from django.urls import reverse

def redirect_to_dashboard(request):
    """
    Redirect user to their appropriate dashboard based on role.
    If user is not authenticated, redirect to login page.
    """
    # Debug information
    print("\n=== DASHBOARD REDIRECT VIEW ===")
    print(f"User authenticated: {request.user.is_authenticated}")
    if request.user.is_authenticated:
        user = request.user
        print(f"User: {user.username}")
        print(f"is_superuser: {user.is_superuser}")
        print(f"is_staff: {user.is_staff}")
        print(f"is_lecturer: {getattr(user, 'is_lecturer', False)}")
        print(f"is_student: {getattr(request.user, 'is_student', False)}")
        print(f"Session data: {dict(request.session.items()) if hasattr(request, 'session') else 'No session'}")
    print("==============================\n")
    
    # If user is not authenticated, redirect to login with next parameter
    if not request.user.is_authenticated:
        next_url = request.GET.get('next', '')
        login_url = reverse('attendance:login')
        if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts=request.get_host()):
            login_url = f"{login_url}?next={next_url}"
        print(f"Not authenticated, redirecting to login: {login_url}")
        return redirect(login_url)
    
    # For authenticated users, redirect based on role
    user = request.user
    
    # Ensure the user has a valid role
    if not any([user.is_superuser, user.is_staff, getattr(user, 'is_lecturer', False), getattr(user, 'is_student', False)]):
        # If user has no valid role, log them out and redirect to login
        from django.contrib.auth import logout
        print("User has no valid role, logging out")
        logout(request)
        messages.error(request, 'Your account is not properly configured. Please contact an administrator.')
        return redirect('attendance:login')
    
    # Redirect based on user role
    if user.is_superuser or user.is_staff:
        print("Redirecting to admin dashboard")
        return redirect('dashboard:admin_dashboard')
    elif hasattr(user, 'is_lecturer') and user.is_lecturer:
        print("Redirecting to lecturer dashboard")
        return redirect('dashboard:lecturer_dashboard')
    elif hasattr(user, 'is_student') and user.is_student:
        print("Redirecting to student dashboard")
        return redirect('dashboard:student_dashboard')
    
    # This should never be reached due to the check above
    print("CRITICAL: User has valid role but no matching dashboard. This should not happen.")
    from django.contrib.auth import logout
    logout(request)
    messages.error(request, 'An error occurred. Please log in again.')
    return redirect('attendance:login')

@login_required
def admin_dashboard(request):
    """Admin dashboard view with comprehensive statistics and analytics."""
    if not request.user.is_superuser:
        return redirect('attendance:login')
    
    # Basic counts with optimized queries
    total_modules = Module.objects.count()
    total_lecturers = User.objects.filter(is_lecturer=True).count()
    total_students = User.objects.filter(is_student=True).count()
    total_qr_codes = QRCode.objects.count()
    
    # Attendance statistics with optimized queries
    attendance_stats = Attendance.objects.aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        late=Count('id', filter=Q(status='late')),
        absent=Count('id', filter=Q(status='absent'))
    )
    
    total_attendance_records = attendance_stats['total']
    present_count = attendance_stats['present']
    late_count = attendance_stats['late']
    absent_count = attendance_stats['absent']
    
    attendance_rate = (present_count / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    # Module statistics with optimized queries
    modules = Module.objects.prefetch_related('qrcodes', 'students').all()
    module_stats = []
    
    # Get attendance data for all modules in a single query
    module_attendance = Attendance.objects.values('qrcode__module')\
        .annotate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            sessions=Count('qrcode', distinct=True)
        )
    
    # Convert to dictionary for faster lookups
    attendance_by_module = {item['qrcode__module']: item for item in module_attendance}
    
    for module in modules:
        module_data = attendance_by_module.get(module.id, {'total': 0, 'present': 0, 'sessions': 0})
        total_sessions = module_data['sessions'] or 1  # Avoid division by zero
        module_attendance_rate = (module_data['present'] / (module_data['total'] or 1)) * 100
        
        module_stats.append({
            'id': module.id,
            'code': module.code,
            'name': module.name,
            'total_sessions': total_sessions,
            'attendance_rate': round(module_attendance_rate, 1),
            'enrolled_students': module.students.count(),
        })
    
    # Sort modules by attendance rate (descending) and get top 5
    module_stats = sorted(module_stats, key=lambda x: x['attendance_rate'], reverse=True)[:5]
    
    # Get recent QR codes with attendance data and related objects
    recent_qrcodes = QRCode.objects.select_related('module', 'lecturer')\
                                 .prefetch_related('attendance_set')\
                                 .order_by('-created_at')[:5]
    
    # Prepare data for charts - Last 30 days attendance trend
    today = timezone.now().date()
    date_range = [today - timezone.timedelta(days=i) for i in range(29, -1, -1)]
    
    # Get daily attendance data in a single query
    daily_data = Attendance.objects.filter(
        timestamp__date__gte=date_range[0],
        timestamp__date__lte=today
    ).values('timestamp__date').annotate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        late=Count('id', filter=Q(status='late'))
    ).order_by('timestamp__date')
    
    # Create a dictionary of date to attendance data
    daily_attendance_dict = {
        item['timestamp__date']: {
            'total': item['total'],
            'present': item['present'],
            'rate': (item['present'] / item['total'] * 100) if item['total'] > 0 else 0
        } for item in daily_data
    }
    
    # Prepare data for the chart and calculate max attendance
    daily_attendance = []
    max_attendance = 0
    for date in date_range:
        if date in daily_attendance_dict:
            rate = round(daily_attendance_dict[date]['rate'], 1)
            daily_attendance.append(rate)
            if rate > max_attendance:
                max_attendance = rate
        else:
            daily_attendance.append(0)
    
    # Student attendance distribution with optimized query
    student_attendance = User.objects.filter(is_student=True)\
        .annotate(
            total_attendance=Count('attendance', filter=Q(attendance__status__in=['present', 'late', 'absent'])),
            present_attendance=Count('attendance', filter=Q(attendance__status='present'))
        )\
        .values('id', 'total_attendance', 'present_attendance')
    
    # Calculate distribution
    attendance_distribution = {
        '90-100%': 0,
        '75-89%': 0,
        '50-74%': 0,
        '0-49%': 0
    }
    
    for student in student_attendance:
        if student['total_attendance'] > 0:
            rate = (student['present_attendance'] / student['total_attendance']) * 100
            if rate >= 90:
                attendance_distribution['90-100%'] += 1
            elif rate >= 75:
                attendance_distribution['75-89%'] += 1
            elif rate >= 50:
                attendance_distribution['50-74%'] += 1
            else:
                attendance_distribution['0-49%'] += 1
    
    # Get module with highest and lowest attendance
    if module_stats:
        best_module = max(module_stats, key=lambda x: x['attendance_rate'])
        worst_module = min(module_stats, key=lambda x: x['attendance_rate'])
    else:
        best_module = worst_module = None
    
    # Get recent activity (last 5 attendance records)
    recent_activity = Attendance.objects.select_related('student', 'qrcode__module')\
                                     .order_by('-timestamp')[:5]
    
    context = {
        'total_modules': total_modules,
        'total_lecturers': total_lecturers,
        'total_students': total_students,
        'total_qr_codes': total_qr_codes,
        'attendance_rate': round(attendance_rate, 1),
        'present_count': present_count,
        'late_count': late_count,
        'absent_count': absent_count,
        'total_attendance_records': total_attendance_records,
        'module_stats': module_stats,
        'recent_qrcodes': recent_qrcodes,
        'date_labels': [date.strftime('%b %d') for date in date_range],
        'daily_attendance': daily_attendance,
        'max_attendance': max_attendance,
        'attendance_distribution': attendance_distribution,
        'attendance_distribution_labels': [
            '90-100%', '75-89%', '50-74%', 'Below 50%'
        ],
        'attendance_distribution_data': [
            attendance_distribution['90-100%'],
            attendance_distribution['75-89%'],
            attendance_distribution['50-74%'],
            attendance_distribution['0-49%'],
        ],
        'current_time': timezone.now(),
        'is_admin': True,
        # Additional stats
        'active_sessions': QRCode.objects.filter(is_active=True).count(),
        'today_attendance': Attendance.objects.filter(
            timestamp__date=today
        ).count()
    }
    return render(request, 'dashboard/admin.html', context)

@login_required
def lecturer_dashboard(request):
    """Lecturer dashboard view with comprehensive statistics and attendance data."""
    if not request.user.is_lecturer and not request.user.is_superuser:
        return redirect('attendance:login')
    
    user = request.user
    now = timezone.now()
    
    # Get all user statistics
    user_stats = {
        'total_lecturers': User.objects.filter(is_lecturer=True).count(),
        'total_students': User.objects.filter(is_student=True).count(),
        'total_admins': User.objects.filter(is_superuser=True).count(),
        'total_users': User.objects.count()
    }
    
    # Get modules taught by this lecturer
    modules = Module.objects.filter(lecturers=user).prefetch_related('students')
    
    # Get active QR codes for this lecturer's modules (sessions from last 48 hours)
    active_sessions = QRCode.objects.filter(
        module__in=modules,
        is_active=True,
        session_date__gte=now - timezone.timedelta(hours=48),
        session_date__lte=now + timezone.timedelta(hours=2)  # Include sessions starting in next 2 hours
    ).select_related('module').order_by('session_date')
    
    # Get recent sessions (last 10)
    recent_sessions = QRCode.objects.filter(
        module__in=modules,
        session_date__lte=now
    ).select_related('module').order_by('-session_date')[:10]
    
    # Get overall attendance statistics
    total_attendance = Attendance.objects.count()
    present_attendance = Attendance.objects.filter(status='present').count()
    overall_attendance_rate = (present_attendance / total_attendance * 100) if total_attendance > 0 else 0
    
    # Calculate attendance statistics
    attendance_stats = []
    total_attendance_rate = 0
    sessions_count = 0
    
    # Get all unique students across all modules
    all_students = set()
    for module in modules:
        all_students.update(module.students.all())
    total_unique_students = len(all_students)
    
    # Calculate attendance for recent sessions
    for qrcode in recent_sessions:
        total_students_in_module = qrcode.module.students.count()
        present_count = Attendance.objects.filter(
            qrcode=qrcode, 
            status='present'
        ).count()
        
        attendance_rate = (present_count / total_students_in_module * 100) if total_students_in_module > 0 else 0
        total_attendance_rate += attendance_rate
        sessions_count += 1
        
        attendance_stats.append({
            'qrcode': qrcode,  # Include the QR code object
            'module': qrcode.module,
            'date': qrcode.session_date,
            'total_students': total_students_in_module,
            'present_count': present_count,
            'attendance_count': present_count,  # For the template
            'attendance_rate': round(attendance_rate, 1)
        })
    
    # Calculate average attendance rate
    avg_attendance_rate = round(total_attendance_rate / sessions_count, 1) if sessions_count > 0 else 0
    
    # Get total modules for the lecturer
    total_modules = modules.count()
    
    # Count active sessions
    active_sessions_count = active_sessions.count()
    
    # Get upcoming sessions for lecturer's modules (next 7 days)
    upcoming_sessions = QRCode.objects.filter(
        module__in=modules,
        session_date__gte=now,
        session_date__lte=now + timezone.timedelta(days=7)
    ).select_related('module', 'lecturer').order_by('session_date')[:5]
    
    # Calculate attendance stats for each module
    modules_with_attendance = []
    total_attendance_rate = 0
    module_count = modules.count()
    
    for module in modules:
        qrcodes = QRCode.objects.filter(module=module)
        total_sessions = qrcodes.count()
        
        if total_sessions == 0:
            module_attendance_rate = 0
        else:
            total_present = Attendance.objects.filter(
                qrcode__in=qrcodes,
                status='present'
            ).count()
            
            total_possible = module.students.count() * total_sessions
            module_attendance_rate = (total_present / total_possible * 100) if total_possible > 0 else 0
            
            total_attendance_rate += module_attendance_rate
        
        modules_with_attendance.append({
            'id': module.id,
            'code': module.code,
            'name': module.name,
            'attendance_rate': module_attendance_rate,
            'total_sessions': total_sessions
        })
    
    avg_attendance_rate = total_attendance_rate / module_count if module_count > 0 else 0
    
    # Get recent sessions for the lecturer's modules with attendance data
    recent_sessions = QRCode.objects.filter(
        module__in=modules
    ).select_related('module').prefetch_related('attendance_set').order_by('-session_date')[:5]
    
    context = {
        'user': user,
        'active_sessions': active_sessions,
        'active_sessions_count': active_sessions_count,
        'recent_sessions': recent_sessions,
        'total_students': total_unique_students,
        'upcoming_sessions': upcoming_sessions,
        'attendance_stats': attendance_stats,
        'total_modules': total_modules,
        'avg_attendance_rate': round(avg_attendance_rate, 1),
        'now': now,
        'total_attendance_entries': sum(stat['present_count'] for stat in attendance_stats),
        'total_sessions': sessions_count,
        'attendance_data': {
            'labels': [f"{stat['module'].code} - {stat['date'].strftime('%b %d')}" for stat in attendance_stats],
            'present': [stat['present_count'] for stat in attendance_stats],
            'absent': [stat['total_students'] - stat['present_count'] for stat in attendance_stats],
            'rates': [stat['attendance_rate'] for stat in attendance_stats]
        },
        'module_count': module_count,
        'is_lecturer': True,
        'modules_with_attendance': modules_with_attendance
    }
    return render(request, 'dashboard/lecturer.html', context)

@login_required
def debug_user_roles(request):
    """Debug view to check user roles"""
    user = request.user
    return JsonResponse({
        'username': user.username,
        'is_authenticated': user.is_authenticated,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'is_lecturer': user.is_lecturer,
        'is_student': user.is_student,
        'groups': list(user.groups.values_list('name', flat=True)),
        'permissions': list(user.get_all_permissions()),
    })

@login_required
def enroll_in_module(request, module_id):
    """Handle module enrollment for students."""
    if not request.user.is_student and not request.user.is_superuser:
        messages.error(request, 'Only students can enroll in modules.')
        return redirect('dashboard:student_dashboard')
    
    module = get_object_or_404(Module, id=module_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'enroll':
            if not module.students.filter(id=request.user.id).exists():
                module.students.add(request.user)
                messages.success(request, f'Successfully enrolled in {module.code} - {module.name}')
            else:
                messages.info(request, f'You are already enrolled in {module.code}')
        elif action == 'unenroll':
            if module.students.filter(id=request.user.id).exists():
                module.students.remove(request.user)
                messages.success(request, f'Successfully unenrolled from {module.code} - {module.name}')
            else:
                messages.info(request, f'You are not enrolled in {module.code}')
    
    return redirect('dashboard:student_dashboard')

def student_dashboard(request):
    """Student dashboard view with active QR codes and attendance statistics."""
    # Debug information
    print("\n=== STUDENT DASHBOARD VIEW ===")
    print(f"User: {request.user.username if request.user.is_authenticated else 'Not authenticated'}")
    print(f"is_authenticated: {request.user.is_authenticated}")
    print(f"is_student: {getattr(request.user, 'is_student', False)}")
    print(f"is_superuser: {getattr(request.user, 'is_superuser', False)}")
    print(f"Session data: {dict(request.session.items()) if hasattr(request, 'session') else 'No session'}")
    
    # If user is not authenticated, redirect to login
    if not request.user.is_authenticated:
        print("User not authenticated, redirecting to login")
        return redirect('attendance:login')
    
    # If user is not a student or superuser, redirect to appropriate dashboard
    if not request.user.is_student and not request.user.is_superuser:
        print("User is not a student, checking other roles")
        if request.user.is_lecturer:
            return redirect('dashboard:lecturer_dashboard')
        elif request.user.is_superuser:
            return redirect('dashboard:admin_dashboard')
        else:
            # If no role matches, log them out and redirect to login
            from django.contrib.auth import logout
            logout(request)
            messages.error(request, 'Your account does not have the required permissions.')
            return redirect('attendance:login')
    
    print("User is authorized to view student dashboard")
    
    user = request.user
    now = timezone.now()
    
    # Get all modules the student is enrolled in with related data
    enrolled_modules = Module.objects.filter(students=user).prefetch_related(
        Prefetch(
            'qrcodes',
            queryset=QRCode.objects.select_related('module', 'lecturer')
                                .filter(is_active=True)
                                .order_by('session_date')
        )
    )
    
    # Get module IDs for filtering
    module_ids = enrolled_modules.values_list('id', flat=True)
    
    # Get all available modules that the student is not enrolled in
    available_modules = Module.objects.exclude(students=user).order_by('code')
    
    # For backward compatibility
    modules = enrolled_modules
    
    # Get time windows for filtering
    time_window = timezone.timedelta(minutes=15)
    future_window = now + time_window
    next_24h = now + timezone.timedelta(hours=24)
    
    # Get active and upcoming QR codes in a single query
    qrcode_queryset = QRCode.objects.filter(
        module_id__in=module_ids,
        is_active=True,
        session_date__lte=next_24h
    ).select_related('module', 'lecturer').order_by('session_date')
    
    # Split into active and upcoming in Python to avoid extra queries
    all_relevant_qrcodes = list(qrcode_queryset)
    active_qrcodes = [
        qr for qr in all_relevant_qrcodes 
        if now - time_window <= qr.session_date <= future_window
    ]
    upcoming_qrcodes = [
        qr for qr in all_relevant_qrcodes 
        if now < qr.session_date <= next_24h
    ]
    
    # Get attendance statistics for all modules in bulk
    from django.db.models import Count, Q, F, Case, When, IntegerField, Value, Subquery, OuterRef
    from django.db.models.functions import Coalesce
    
    # Get attendance counts for all modules in a single query
    attendance_counts = (
        QRCode.objects
        .filter(module__in=module_ids)
        .values('module')
        .annotate(
            total_sessions=Count('id'),
            attended_sessions=Count(
                'attendance',
                filter=Q(attendance__student=user, attendance__status='present')
            )
        )
    )
    
    # Convert to a dictionary for easier lookup
    attendance_dict = {
        item['module']: {
            'total': item['total_sessions'],
            'attended': item['attended_sessions'],
            'percentage': round((item['attended_sessions'] / item['total_sessions'] * 100), 1) 
                         if item['total_sessions'] > 0 else 0
        }
        for item in attendance_counts
    }
    
    # Get next sessions for all modules in a single query (SQLite compatible)
    from django.db.models import Min, Subquery, OuterRef
    
    # First, get the minimum session_date for each module
    min_dates = (
        QRCode.objects
        .filter(
            module_id=OuterRef('module_id'),
            session_date__gte=now,
            is_active=True
        )
        .order_by('session_date')
        .values('session_date')[:1]
    )
    
    # Then get the QRCode objects with those minimum dates
    next_sessions_qs = (
        QRCode.objects
        .filter(
            module_id__in=module_ids,
            session_date__in=Subquery(min_dates),
            is_active=True
        )
        .order_by('module_id', 'session_date')
    )
    
    # Create a dictionary of module_id to next session date
    next_session_dates = {}
    for session in next_sessions_qs:
        if session.module_id not in next_session_dates:
            next_session_dates[session.module_id] = session.session_date
    
    # Prepare attendance stats
    attendance_stats = {}
    total_percentage = 0
    module_count = 0
    total_attended = 0
    next_sessions = []
    
    for module in modules:
        module_stats = attendance_dict.get(module.id, {'total': 0, 'attended': 0, 'percentage': 0})
        next_session = next_session_dates.get(module.id)
        
        if next_session:
            next_sessions.append(next_session)
        
        attendance_stats[module] = {
            'total_sessions': module_stats['total'],
            'attended': module_stats['attended'],
            'percentage': module_stats['percentage'],
            'next_session': next_session
        }
        
        if module_stats['total'] > 0:
            total_percentage += module_stats['percentage']
            module_count += 1
            total_attended += module_stats['attended']
    
    # Calculate overall attendance percentage
    overall_attendance = round(total_percentage / module_count, 1) if module_count > 0 else 0
    
    # Get recent attendance records for the student with limit
    recent_attendance = list(
        Attendance.objects
        .filter(student=user)
        .select_related('qrcode', 'qrcode__module')
        .order_by('-timestamp')[:5]
    )
    
    # Get the next upcoming session
    next_session = min(next_sessions) if next_sessions else None
    
    context = {
        'modules': enrolled_modules,
        'available_modules': available_modules,
        'active_qrcodes': active_qrcodes,
        'upcoming_qrcodes': upcoming_qrcodes,
        'attendance_stats': attendance_stats,
        'overall_attendance': overall_attendance,
        'total_attended': total_attended,
        'next_session': next_session,
        'recent_attendance': recent_attendance,
        'is_student': True,
        'now': now,
        'time_window': time_window
    }
    return render(request, 'dashboard/student.html', context)

@csrf_exempt
@login_required
def submit_attendance(request, qrcode_id):
    """Handle QR code submission with authentication."""
    if not request.user.is_student:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get the QR code object
            try:
                qr_code = QRCode.objects.get(id=qrcode_id, is_active=True)
            except QRCode.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Invalid or expired QR code'}, status=404)
            
            # Check if QR code is expired
            if qr_code.expiry_time < timezone.now():
                return JsonResponse({
                    'success': False, 
                    'error': 'This QR code has expired'
                }, status=400)
            
            # Check if the student is enrolled in the module
            if not qr_code.module.enrolled_students.filter(id=request.user.id).exists():
                return JsonResponse({
                    'success': False, 
                    'error': 'You are not enrolled in this module'
                }, status=403)
            
            # Record attendance if not already recorded
            attendance, created = Attendance.objects.get_or_create(
                student=request.user,
                qr_code=qr_code,
                defaults={'is_present': True}
            )
            
            if not created and not attendance.is_present:
                attendance.is_present = True
                attendance.save()
                
            return JsonResponse({
                'success': True,
                'message': 'Attendance recorded successfully',
                'module_name': qr_code.module.name,
                'lecturer': qr_code.lecturer.get_full_name() or qr_code.lecturer.username
            })
        
        except QRCode.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid or expired QR code'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@require_http_methods(["POST"])
def generate_qr_code(request):
    """Generate a new QR code for attendance."""
    try:
        data = json.loads(request.body)
        module_id = data.get('module_id')
        duration = int(data.get('duration', 5))  # Default to 5 minutes
        
        # Get the module
        module = get_object_or_404(Module, id=module_id, lecturer=request.user)
        
        # Create a new QR code
        qr_code = QRCode.objects.create(
            module=module,
            lecturer=request.user,
            expires_at=timezone.now() + timedelta(minutes=duration)
        )
        
        # Generate QR code data
        qr_data = {
            'id': str(qr_code.id),
            'module': module.code,
            'expires': qr_code.expires_at.isoformat(),
        }
        
        # Create QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save image to bytes
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_image = buffer.getvalue()
        
        # In a real app, you might want to save this to a file or storage
        # For now, we'll just return the data URL
        import base64
        qr_code_data_url = f"data:image/png;base64,{base64.b64encode(qr_code_image).decode('utf-8')}"
        
        return JsonResponse({
            'success': True,
            'qr_code_id': str(qr_code.id),
            'expires_at': qr_code.expires_at.isoformat(),
            'module_name': module.name,
            'qr_code_image': qr_code_data_url,
            'url': request.build_absolute_uri(reverse('dashboard:submit_attendance', args=[qr_code.id]))
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def end_session(request, session_id):
    """End an active QR code session."""
    try:
        qr_code = get_object_or_404(QRCode, id=session_id, lecturer=request.user, is_active=True)
        qr_code.is_active = False
        qr_code.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Session ended successfully',
            'session_id': str(qr_code.id)
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def get_active_sessions(request):
    """Get all active QR code sessions for the lecturer."""
    try:
        active_sessions = QRCode.objects.filter(
            lecturer=request.user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).select_related('module').order_by('expires_at')
        
        sessions_data = [{
            'id': str(session.id),
            'module_name': session.module.name,
            'module_code': session.module.code,
            'expires_at': session.expires_at.isoformat(),
            'time_remaining': (session.expires_at - timezone.now()).total_seconds(),
            'url': request.build_absolute_uri(reverse('dashboard:submit_attendance', args=[session.id]))
        } for session in active_sessions]
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def view_schedule(request):
    """View to display the weekly class schedule and upcoming classes"""
    # Get the current day and time
    now = timezone.now()
    current_day = now.strftime('%A').lower()
    current_time = now.time()
    
    # Get modules for the current user
    if request.user.is_lecturer:
        user_modules = Module.objects.filter(lecturer=request.user)
        # Get all classes for modules taught by the lecturer
        user_classes = ClassSchedule.objects.filter(
            module__in=user_modules,
            is_active=True
        )
    else:
        # Get all classes for modules the student is enrolled in
        user_classes = ClassSchedule.objects.filter(
            module__enrolled_students=request.user,
            is_active=True
        )
    
    # Get the weekly schedule for user's modules
    weekly_schedule = {day[0]: [] for day in ClassSchedule.DAYS_OF_WEEK}
    for class_schedule in user_classes.order_by('day_of_week', 'start_time'):
        weekly_schedule[class_schedule.day_of_week].append(class_schedule)
    
    # Get upcoming classes (next 4 hours)
    upcoming_time = (now + timedelta(hours=4)).time()
    upcoming_classes = []
    
    # Convert day names to match our model
    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    current_day_index = days_order.index(current_day) if current_day in days_order else -1
    
    # Check today's remaining classes
    if current_day_index >= 0:
        today_classes = user_classes.filter(
            day_of_week=current_day,
            start_time__gte=current_time
        ).order_by('start_time')
        
        for cls in today_classes:
            class_time = datetime.combine(now.date(), cls.start_time)
            time_diff = (class_time - now).total_seconds() / 60  # in minutes
            upcoming_classes.append({
                'class_obj': cls,
                'time_until': time_diff,
                'is_today': True,
                'start_datetime': class_time
            })
    
    # Add classes from upcoming days (next 7 days)
    for i in range(1, 7):
        next_day_index = (current_day_index + i) % 7
        if next_day_index >= len(days_order):
            continue
            
        day_name = days_order[next_day_index]
        day_classes = user_classes.filter(
            day_of_week=day_name
        ).order_by('start_time')
        
        days_to_add = (7 + next_day_index - current_day_index) % 7
        class_date = now.date() + timedelta(days=days_to_add)
        
        for cls in day_classes:
            class_time = datetime.combine(class_date, cls.start_time)
            time_diff = (class_time - now).total_seconds() / 60  # in minutes
            upcoming_classes.append({
                'class_obj': cls,
                'time_until': time_diff,
                'is_today': False,
                'start_datetime': class_time
            })
    
    # Sort all upcoming classes by time
    upcoming_classes.sort(key=lambda x: x['time_until'])
    
    # Get the next 3 upcoming classes
    next_classes = upcoming_classes[:3]
    
    # Get unique modules for the filter dropdown
    modules = user_classes.values_list('module', 'module__name').distinct()
    
    context = {
        'weekly_schedule': weekly_schedule,
        'next_classes': next_classes,
        'current_day': current_day,
        'current_time': current_time,
        'modules': [{'id': m[0], 'name': m[1]} for m in modules],
        'now': now,
    }
    
    return render(request, 'dashboard/schedule.html', context)

@login_required
def module_detail(request, module_id):
    """View to display module details and course outline"""
    # Get the module, ensuring the user has permission to view it
    if request.user.is_lecturer:
        module = get_object_or_404(Module, id=module_id, lecturers=request.user)
    else:
        module = get_object_or_404(Module, id=module_id, students=request.user)
    
    # Get upcoming sessions for this module
    upcoming_sessions = QRCode.objects.filter(
        module=module,
        session_date__gte=timezone.now()
    ).order_by('session_date')
    
    # Get attendance stats for the student (if not lecturer)
    attendance_stats = None
    if not request.user.is_lecturer:
        total_sessions = QRCode.objects.filter(module=module).count()
        attended_sessions = Attendance.objects.filter(
            student=request.user,
            qrcode__module=module,
            status='present'
        ).count()
        
        if total_sessions > 0:
            attendance_percentage = (attended_sessions / total_sessions) * 100
            attendance_stats = {
                'total_sessions': total_sessions,
                'attended_sessions': attended_sessions,
                'attendance_percentage': round(attendance_percentage, 2)
            }
    
    context = {
        'module': module,
        'upcoming_sessions': upcoming_sessions,
        'attendance_stats': attendance_stats,
        'is_lecturer': request.user.is_lecturer,
    }
    
    return render(request, 'dashboard/module_detail.html', context)

@login_required
def get_attendance_stats(request):
    """
    Display attendance statistics for the lecturer's modules.
    Supports both HTML and JSON responses based on the request type.
    """
    if not request.user.is_authenticated:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Not authenticated'}, status=401)
        return redirect('account_login')
    
    try:
        # Get all modules taught by this lecturer
        modules = Module.objects.filter(lecturers=request.user).prefetch_related('students')
        
        # Initialize module statistics
        module_stats = []
        total_students = 0
        total_sessions = 0
        total_attendance = 0
        
        # Get date range for filtering (last 30 days by default)
        end_date = timezone.now()
        start_date = end_date - timezone.timedelta(days=30)
        
        # Get attendance data for each module
        for module in modules:
            # Get all QR codes for this module within date range
            qr_codes = QRCode.objects.filter(
                module=module,
                created_at__range=(start_date, end_date)
            )
            
            # Get total number of sessions for this module
            module_total_sessions = qr_codes.count()
            
            # Get attendance records for this module
            attendance_records = Attendance.objects.filter(
                qrcode__in=qr_codes
            ).select_related('student')
            
            # Get unique students enrolled in this module
            students = module.students.all()
            student_count = students.count()
            total_students += student_count
            total_sessions += module_total_sessions
            
            # Calculate attendance statistics
            present_count = attendance_records.filter(status='present').count()
            late_count = attendance_records.filter(status='late').count()
            absent_count = attendance_records.filter(status='absent').count()
            total_attendance += present_count + late_count
            
            # Calculate attendance percentage
            total_records = present_count + late_count + absent_count
            attendance_percentage = (present_count / total_records * 100) if total_records > 0 else 0
            
            # Get recent attendance for this module
            recent_attendance = attendance_records.order_by('-timestamp')[:5]
            
            module_stats.append({
                'id': module.id,
                'code': module.code,
                'name': module.name,
                'student_count': student_count,
                'total_sessions': module_total_sessions,
                'present_count': present_count,
                'late_count': late_count,
                'absent_count': absent_count,
                'attendance_percentage': round(attendance_percentage, 1),
                'recent_attendance': recent_attendance
            })
        
        # Calculate overall statistics
        overall_stats = {
            'total_modules': modules.count(),
            'total_students': total_students,
            'total_sessions': total_sessions,
            'total_attendance': total_attendance,
            'attendance_percentage': round((total_attendance / (total_sessions * total_students) * 100) 
                                        if total_sessions > 0 and total_students > 0 else 0, 1)
        }
        
        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'modules': module_stats,
                'overall_stats': overall_stats
            }, safe=False)
        
        # Return HTML response for regular requests
        context = {
            'module_stats': module_stats,
            'overall_stats': overall_stats,
            'start_date': start_date.date(),
            'end_date': end_date.date(),
            'current_date': timezone.now().date()
        }
        
        return render(request, 'dashboard/lecturer_attendance.html', context)
        
    except Exception as e:
        logger.error(f"Error in get_attendance_stats view: {str(e)}", exc_info=True)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'An error occurred while fetching attendance statistics.'}, status=500)
        messages.error(request, 'An error occurred while loading attendance statistics.')
        return redirect('dashboard:lecturer_dashboard')

@login_required
def student_schedule(request):
    """
    Display the student's class schedule.
    """
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:index')
    
    try:
        # Get the current date and time
        now = timezone.now()
        
        # Get all modules the student is enrolled in
        enrolled_modules = request.user.enrolled_modules.all()
        
        # Get all class schedules for these modules
        schedules = ClassSchedule.objects.filter(
            module__in=enrolled_modules
        ).select_related('module').order_by('day_of_week', 'start_time')
        
        # Get today's schedule
        today_weekday = now.weekday() + 1  # Convert from 0-6 to 1-7
        today_schedule = schedules.filter(day_of_week=today_weekday)
        
        # Get upcoming classes (next 7 days)
        upcoming_classes = []
        for i in range(1, 8):
            target_date = now + timedelta(days=i)
            target_weekday = target_date.weekday() + 1
            
            classes = schedules.filter(day_of_week=target_weekday)
            if classes.exists():
                for cls in classes:
                    upcoming_classes.append({
                        'date': target_date,
                        'class': cls,
                        'is_today': i == 1
                    })
        
        # Sort upcoming classes by date and time
        upcoming_classes.sort(key=lambda x: (x['date'], x['class'].start_time))
        
        context = {
            'today_schedule': today_schedule,
            'upcoming_classes': upcoming_classes[:7],  # Limit to next 7 classes
            'current_time': now.time(),
            'current_date': now.date()
        }
        
        return render(request, 'dashboard/student_schedule.html', context)
        
    except Exception as e:
        logger.error(f"Error in student_schedule view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while loading your schedule.')
        return redirect('dashboard:student_dashboard')

@login_required
def student_attendance_records(request):
    """
    Display the student's attendance records across all enrolled modules.
    """
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('dashboard:index')
    
    try:
        # Get current datetime for filtering
        now = timezone.now()
        
        # Get all modules the student is enrolled in
        enrolled_modules = request.user.enrolled_modules.all()
        module_ids = enrolled_modules.values_list('id', flat=True)
        
        # Get all attendance records for the student
        attendance_records = Attendance.objects.filter(
            student=request.user,
            qrcode__module_id__in=module_ids
        ).select_related('qrcode', 'qrcode__module').order_by('-timestamp')
        
        # Group attendance by module
        attendance_by_module = {}
        for record in attendance_records:
            module_id = record.qrcode.module.id
            if module_id not in attendance_by_module:
                attendance_by_module[module_id] = {
                    'module': record.qrcode.module,
                    'records': [],
                    'stats': {
                        'total': 0,
                        'present': 0,
                        'late': 0,
                        'absent': 0,
                        'percentage': 0
                    }
                }
            
            attendance_by_module[module_id]['records'].append(record)
            attendance_by_module[module_id]['stats']['total'] += 1
            
            if record.status == 'present':
                attendance_by_module[module_id]['stats']['present'] += 1
            elif record.status == 'late':
                attendance_by_module[module_id]['stats']['late'] += 1
            elif record.status == 'absent':
                attendance_by_module[module_id]['stats']['absent'] += 1
        
        # Calculate percentages for each module
        for module_id, data in attendance_by_module.items():
            total = data['stats']['total']
            present = data['stats']['present']
            data['stats']['percentage'] = round((present / total * 100) if total > 0 else 0, 1)
        
        # Get recent attendance (last 5 records across all modules)
        recent_attendance = attendance_records[:5]
        
        # Calculate overall statistics
        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        late_count = attendance_records.filter(status='late').count()
        absent_count = attendance_records.filter(status='absent').count()
        
        overall_stats = {
            'total': total_records,
            'present': present_count,
            'late': late_count,
            'absent': absent_count,
            'percentage': round((present_count / total_records * 100) if total_records > 0 else 0, 1)
        }
        
        context = {
            'attendance_by_module': attendance_by_module,
            'recent_attendance': recent_attendance,
            'overall_stats': overall_stats,
            'current_date': now.date()
        }
        
        return render(request, 'dashboard/student_attendance.html', context)
        
    except Exception as e:
        logger.error(f"Error in student_attendance_records view: {str(e)}", exc_info=True)
        messages.error(request, 'An error occurred while loading your attendance records.')
        return redirect('dashboard:student_dashboard')


@login_required
def student_profile(request):
    """
    Display and allow editing of the student's profile information.
    """
    if not hasattr(request.user, 'is_student') or not request.user.is_student:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get the student's enrolled modules
    enrolled_modules = request.user.enrolled_modules.all().order_by('code')
    
    # Get attendance statistics
    attendance_records = Attendance.objects.filter(student=request.user)
    total_sessions = attendance_records.count()
    present_count = attendance_records.filter(status='present').count()
    attendance_percentage = (present_count / total_sessions * 100) if total_sessions > 0 else 0
    
    context = {
        'page_title': 'My Profile',
        'active_tab': 'profile',
        'enrolled_modules': enrolled_modules,
        'total_sessions': total_sessions,
        'present_count': present_count,
        'attendance_percentage': round(attendance_percentage, 1),
        'user': request.user
    }
    
    return render(request, 'dashboard/student_profile.html', context)


@login_required
def lecturer_profile(request):
    """
    Display and allow editing of the lecturer's profile information.
    """
    if not hasattr(request.user, 'is_lecturer') or not request.user.is_lecturer:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('dashboard:index')
    
    # Get the lecturer's teaching modules
    teaching_modules = request.user.modules.all().order_by('code')
    
    # Get session statistics
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    sessions_this_month = QRCode.objects.filter(
        lecturer=request.user,
        created_at__gte=start_of_month
    ).count()
    
    context = {
        'page_title': 'My Profile',
        'active_tab': 'profile',
        'teaching_modules': teaching_modules,
        'sessions_this_month': sessions_this_month,
        'user': request.user
    }
    
    return render(request, 'dashboard/lecturer_profile.html', context)
