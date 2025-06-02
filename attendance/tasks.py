import logging
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from .models import QRCode, Attendance, Module
from django.db.models import Count, F, Q
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def deactivate_expired_qrcodes(self):
    """
    Task to deactivate expired QR codes
    """
    try:
        now = timezone.now()
        expired_qrs = QRCode.objects.filter(
            is_active=True,
            session_date__lt=now - timedelta(minutes=F('expiration_minutes'))
        )
        
        count = expired_qrs.update(is_active=False)
        logger.info(f"Deactivated {count} expired QR codes")
        return f"Deactivated {count} expired QR codes"
    except Exception as exc:
        logger.error(f"Error deactivating QR codes: {exc}")
        self.retry(exc=exc)

@shared_task
def generate_daily_attendance_reports():
    """
    Generate daily attendance reports for all modules
    """
    from django.template.loader import render_to_string
    from django.core.mail import EmailMessage
    from django.conf import settings
    
    # Calculate date range
    today = timezone.now().date()
    start_date = today - timedelta(days=1)
    
    # Get all modules with attendance in the past day
    modules = Module.objects.filter(
        qrcodes__attendance__timestamp__date__gte=start_date,
        qrcodes__attendance__timestamp__date__lt=today
    ).distinct()
    
    for module in modules:
        # Get all QR codes for this module in the date range
        qr_codes = QRCode.objects.filter(
            module=module,
            session_date__date__gte=start_date,
            session_date__date__lt=today
        )
        
        # Get attendance data
        attendance_data = []
        for qr in qr_codes:
            attendance_count = Attendance.objects.filter(
                qrcode=qr,
                status='present'
            ).count()
            
            attendance_data.append({
                'date': qr.session_date,
                'total_students': qr.module.students.count(),
                'present_count': attendance_count,
                'attendance_percentage': (attendance_count / qr.module.students.count() * 100) if qr.module.students.count() > 0 else 0
            })
        
        # Generate report
        context = {
            'module': module,
            'date': today,
            'attendance_data': attendance_data,
            'total_sessions': len(attendance_data),
            'avg_attendance': sum(d['attendance_percentage'] for d in attendance_data) / len(attendance_data) if attendance_data else 0,
        }
        
        # Render HTML email
        html_content = render_to_string('attendance/email/daily_report.html', context)
        
        # Send email to lecturers
        for lecturer in module.lecturers.all():
            if lecturer.email:
                try:
                    msg = EmailMessage(
                        f"Daily Attendance Report - {module.code} - {today}",
                        html_content,
                        settings.DEFAULT_FROM_EMAIL,
                        [lecturer.email]
                    )
                    msg.content_subtype = "html"
                    msg.send(fail_silently=False)
                    logger.info(f"Sent daily report for {module.code} to {lecturer.email}")
                except Exception as e:
                    logger.error(f"Error sending email to {lecturer.email}: {e}")
    
    return f"Generated reports for {modules.count()} modules"

@shared_task
def process_attendance_async(attendance_id, biometric_data=None):
    """
    Process attendance asynchronously with optional biometric verification
    """
    from .models import Attendance
    
    try:
        attendance = Attendance.objects.get(id=attendance_id)
        
        # Simulate biometric verification if data provided
        if biometric_data:
            # In a real app, this would call your biometric verification service
            attendance.biometric_verified = True
            attendance.status = 'present'
            attendance.save(update_fields=['biometric_verified', 'status'])
            
            # Update cache
            cache_key = f'attendance_{attendance_id}_status'
            cache.set(cache_key, 'verified', timeout=3600)  # Cache for 1 hour
            
            return f"Attendance {attendance_id} verified successfully"
        
        return f"No biometric data provided for attendance {attendance_id}"
        
    except Attendance.DoesNotExist:
        logger.error(f"Attendance record {attendance_id} not found")
        return f"Attendance record {attendance_id} not found"
    except Exception as e:
        logger.error(f"Error processing attendance {attendance_id}: {e}")
        raise

@shared_task
def update_attendance_stats():
    """
    Update cached attendance statistics
    """
    from django.core.cache import cache
    
    # Update module statistics
    modules = Module.objects.all()
    for module in modules:
        # Calculate attendance percentage for the module
        attendance_percentage = module.qrcodes.aggregate(
            avg_attendance=Avg('attendance__status')
        )['avg_attendance'] or 0
        
        # Cache the result for 1 hour
        cache_key = f'module_{module.id}_attendance_stats'
        cache.set(cache_key, {
            'attendance_percentage': attendance_percentage,
            'last_updated': timezone.now().isoformat(),
        }, timeout=3600)
    
    return f"Updated attendance stats for {modules.count()} modules"
