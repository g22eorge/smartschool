from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from datetime import datetime, timedelta

from ..models import QRCode, Attendance, User, Module
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    try:
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'is_lecturer': user.is_lecturer,
                    'is_student': user.is_student,
                }
            })
        else:
            return JsonResponse({'success': False, 'error': 'Invalid credentials'}, status=401)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def api_logout(request):
    auth_logout(request)
    return JsonResponse({'success': True})

@login_required
def api_get_modules(request):
    if request.user.is_lecturer or request.user.is_superuser:
        modules = Module.objects.filter(lecturers=request.user)
    else:
        modules = Module.objects.filter(students=request.user)
    
    return JsonResponse({
        'success': True,
        'modules': [{
            'id': module.id,
            'code': module.code,
            'name': module.name,
            'description': module.description
        } for module in modules]
    })

@login_required
def api_generate_qr(request, module_id):
    try:
        module = Module.objects.get(id=module_id)
        if request.user not in module.lecturers.all() and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        # Create a new QR code
        qr_code = QRCode.objects.create(
            module=module,
            lecturer=request.user,
            is_active=True,
            expires_at=datetime.now() + timedelta(minutes=30)
        )
        
        return JsonResponse({
            'success': True,
            'qr_code': {
                'id': qr_code.id,
                'module_id': qr_code.module.id,
                'lecturer_id': qr_code.lecturer.id,
                'is_active': qr_code.is_active,
                'expires_at': qr_code.expires_at.isoformat(),
                'created_at': qr_code.created_at.isoformat()
            }
        })
    except Module.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Module not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def api_record_attendance(request, qr_code_id):
    try:
        qr_code = QRCode.objects.get(id=qr_code_id, is_active=True)
        
        # Check if QR code has expired
        if qr_code.expires_at < datetime.now(qr_code.expires_at.tzinfo):
            return JsonResponse({'success': False, 'error': 'QR code has expired'}, status=400)
        
        # Check if attendance is already recorded
        if Attendance.objects.filter(qrcode=qr_code, student=request.user).exists():
            return JsonResponse({'success': False, 'error': 'Attendance already recorded'}, status=400)
        
        # Record attendance
        attendance = Attendance.objects.create(
            qrcode=qr_code,
            student=request.user,
            status='present',
            timestamp=datetime.now()
        )
        
        return JsonResponse({
            'success': True,
            'attendance': {
                'id': attendance.id,
                'student_id': attendance.student.id,
                'qr_code_id': attendance.qrcode.id,
                'status': attendance.status,
                'timestamp': attendance.timestamp.isoformat()
            }
        })
    except QRCode.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Invalid or inactive QR code'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
