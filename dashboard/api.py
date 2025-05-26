from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
import random
from django.db.models import Count, F, ExpressionWrapper, DecimalField
from attendance.models import QRCode, Module, Attendance

# Dummy data generators
def generate_dummy_modules(lecturer_id):
    return [
        {
            'id': f'mod_{i+1}_{lecturer_id}',
            'code': f'CS{400 + i}',
            'name': f'Computer Science {400 + i} - {["Algorithms", "Database Systems", "Web Development", "AI", "Networking"][i % 5]}',
            'students_count': random.randint(15, 45)
        } for i in range(5)
    ]

def generate_dummy_sessions(modules, count=10):
    sessions = []
    now = timezone.now()
    
    for i in range(count):
        module = random.choice(modules)
        session_date = now - timedelta(days=random.randint(0, 30), hours=random.randint(1, 24))
        is_active = i == 0  # Make first session active
        
        sessions.append({
            'id': f'sess_{i+1}_{module["id"]}',
            'module_id': module['id'],
            'module_code': module['code'],
            'module_name': module['name'],
            'start_time': (session_date - timedelta(hours=1.5)).isoformat(),
            'end_time': (session_date + timedelta(hours=1.5)).isoformat() if not is_active else None,
            'session_date': session_date.isoformat(),
            'is_active': is_active,
            'total_students': module['students_count'],
            'present_count': random.randint(5, module['students_count'] - 3) if not is_active else 0,
            'location': f'Room {random.randint(100, 500)}-{chr(65 + random.randint(0, 5))}'
        })
    
    return sorted(sessions, key=lambda x: x['session_date'], reverse=True)

def generate_dummy_attendance_reports(modules, sessions):
    reports = []
    
    for module in modules:
        module_sessions = [s for s in sessions if s['module_id'] == module['id']]
        total_sessions = len(module_sessions)
        
        if not module_sessions:
            attendance_rate = 0
        else:
            total_possible = sum(s['total_students'] for s in module_sessions)
            total_present = sum(s['present_count'] for s in module_sessions)
            attendance_rate = round((total_present / total_possible * 100) if total_possible > 0 else 0, 1)
        
        reports.append({
            'code': module['code'],
            'name': module['name'],
            'total_sessions': total_sessions,
            'total_students': module['students_count'],
            'attendance_rate': attendance_rate,
            'trend': random.choice(['up', 'down', 'stable']),
            'trend_value': round(random.uniform(0.1, 5.0), 1)
        })
    
    return reports

@login_required
def get_recent_sessions(request):
    # Generate dummy modules for this lecturer
    modules = generate_dummy_modules(request.user.id)
    
    # Generate dummy sessions for these modules
    sessions = generate_dummy_sessions(modules, count=10)
    
    # Prepare response data
    sessions_data = [{
        'id': session['id'],
        'module_id': session['module_id'],
        'module_code': session['module_code'],
        'module_name': session['module_name'],
        'start_time': session['start_time'],
        'end_time': session['end_time'],
        'session_date': session['session_date'],
        'is_active': session['is_active'],
        'total_students': session['total_students'],
        'present_count': session['present_count'],
        'location': session['location']
    } for session in sessions]
    
    return JsonResponse({
        'status': 'success',
        'sessions': sessions_data
    })

@login_required
def get_attendance_reports(request):
    # Generate dummy modules for this lecturer
    modules = generate_dummy_modules(request.user.id)
    
    # Generate dummy sessions for these modules
    sessions = generate_dummy_sessions(modules, count=15)
    
    # Generate attendance reports
    reports = generate_dummy_attendance_reports(modules, sessions)
    
    return JsonResponse({
        'status': 'success',
        'reports': reports
    })

@login_required
def get_dashboard_stats(request):
    # Generate dummy modules for this lecturer
    modules = generate_dummy_modules(request.user.id)
    
    # Generate dummy sessions for these modules
    sessions = generate_dummy_sessions(modules, count=15)
    
    # Calculate stats
    active_sessions = [s for s in sessions if s['is_active']]
    recent_sessions = sorted(sessions, key=lambda x: x['session_date'], reverse=True)[:5]
    
    # Calculate attendance rate across all modules
    total_students = sum(m['students_count'] for m in modules)
    total_sessions = len(sessions)
    total_present = sum(s['present_count'] for s in sessions if not s['is_active'])
    total_possible = sum(s['total_students'] for s in sessions if not s['is_active'])
    attendance_rate = round((total_present / total_possible * 100) if total_possible > 0 else 0, 1)
    
    return JsonResponse({
        'status': 'success',
        'stats': {
            'total_modules': len(modules),
            'total_students': total_students,
            'total_sessions': total_sessions,
            'active_sessions': len(active_sessions),
            'attendance_rate': attendance_rate,
            'recent_sessions': [{
                'id': s['id'],
                'module_code': s['module_code'],
                'module_name': s['module_name'],
                'date': s['session_date'],
                'present_count': s['present_count'],
                'total_students': s['total_students'],
                'is_active': s['is_active']
            } for s in recent_sessions],
            'active_sessions_list': [{
                'id': s['id'],
                'module_code': s['module_code'],
                'module_name': s['module_name'],
                'start_time': s['start_time'],
                'location': s['location']
            } for s in active_sessions]
        }
    })
