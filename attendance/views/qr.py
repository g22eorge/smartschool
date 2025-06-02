from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
import qrcode
import json
import uuid
from io import BytesIO
from django.core.files.base import ContentFile
from ..models import QRCode, Module, Attendance
from datetime import timedelta

@login_required
def generate_qr(request, module_id=None):
    if request.user.is_superuser:
        modules = Module.objects.all()
    else:
        modules = Module.objects.filter(lecturers=request.user)
    
    if module_id:
        module = get_object_or_404(Module, id=module_id)
        if not request.user.is_superuser and request.user not in module.lecturers.all():
            messages.error(request, 'You do not have permission to generate QR codes for this module.')
            return redirect('attendance:generate_qr')
        
        # Create a new QR code
        qr_data = {
            'module_id': str(module.id),
            'lecturer_id': str(request.user.id),
            'timestamp': str(timezone.now().timestamp()),
            'uuid': str(uuid.uuid4())
        }
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(json.dumps(qr_data))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save the QR code to the database
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code = QRCode(
            module=module,
            lecturer=request.user,
            is_active=True,
            expires_at=timezone.now() + timedelta(minutes=30)
        )
        qr_code.qr_code.save(f'qr_{uuid.uuid4()}.png', ContentFile(buffer.getvalue()), save=False)
        qr_code.save()
        
        messages.success(request, f'QR code generated for {module.code} - {module.name}')
        return redirect('attendance:view_qr', qr_id=qr_code.id)
    
    return render(request, 'attendance/generate_qr.html', {'modules': modules})

@login_required
def view_qr(request, qr_id):
    qr_code = get_object_or_404(QRCode, id=qr_id)
    if not request.user.is_superuser and request.user != qr_code.lecturer:
        messages.error(request, 'You do not have permission to view this QR code.')
        return redirect('attendance:generate_qr')
    
    return render(request, 'attendance/view_qr.html', {'qr_code': qr_code})

@login_required
def deactivate_qr(request, qr_id):
    qr_code = get_object_or_404(QRCode, id=qr_id)
    if not request.user.is_superuser and request.user != qr_code.lecturer:
        messages.error(request, 'You do not have permission to deactivate this QR code.')
        return redirect('attendance:generate_qr')
    
    qr_code.is_active = False
    qr_code.save()
    messages.success(request, 'QR code has been deactivated.')
    return redirect('attendance:qr_history')

@login_required
def qr_history(request, module_id=None):
    if module_id:
        module = get_object_or_404(Module, id=module_id)
        if not request.user.is_superuser and request.user not in module.lecturers.all():
            messages.error(request, 'You do not have permission to view this module\'s QR history.')
            return redirect('attendance:qr_history')
        qr_codes = QRCode.objects.filter(module=module).order_by('-created_at')
    else:
        if request.user.is_superuser:
            qr_codes = QRCode.objects.all().order_by('-created_at')
        else:
            qr_codes = QRCode.objects.filter(lecturer=request.user).order_by('-created_at')
    
    return render(request, 'attendance/qr_history.html', {'qr_codes': qr_codes, 'module_id': module_id})
