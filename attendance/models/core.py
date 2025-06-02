"""
Core models for the SmartSchool attendance system.
"""
import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Module(models.Model):
    """
    Represents a course module in the system.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('module code'), max_length=20, unique=True)
    name = models.CharField(_('module name'), max_length=200)
    description = models.TextField(_('description'), blank=True)
    
    # Relationships
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='enrolled_modules',
        limit_choices_to={'is_staff': False},
        verbose_name=_('students')
    )
    lecturers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='teaching_modules',
        limit_choices_to={'is_staff': True},
        verbose_name=_('lecturers')
    )
    
    # Attendance settings
    attendance_threshold = models.PositiveSmallIntegerField(
        _('attendance threshold (%)'),
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text=_('Minimum attendance percentage required to pass the module')
    )
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('module')
        verbose_name_plural = _('modules')
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """
        Validate the model before saving.
        """
        super().clean()
        self.code = self.code.upper()
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('module_detail', kwargs={'pk': self.pk})
    
    def get_attendance_stats(self):
        """
        Calculate attendance statistics for this module.
        """
        from django.db.models import Count, F, ExpressionWrapper, FloatField
        from django.db.models.functions import Coalesce
        
        # Get all students enrolled in this module
        students = self.students.all()
        total_sessions = self.qrcodes.count()
        
        # Calculate attendance for each student
        attendance_data = []
        
        for student in students:
            attended_sessions = self.qrcodes.filter(
                attendance__student=student,
                attendance__status__in=['PRESENT', 'LATE']
            ).count()
            
            attendance_percentage = (
                (attended_sessions / total_sessions * 100) 
                if total_sessions > 0 else 0
            )
            
            attendance_data.append({
                'student': student,
                'attended_sessions': attended_sessions,
                'total_sessions': total_sessions,
                'attendance_percentage': attendance_percentage,
                'is_above_threshold': attendance_percentage >= self.attendance_threshold
            })
        
        # Sort by attendance percentage (descending)
        attendance_data.sort(key=lambda x: x['attendance_percentage'], reverse=True)
        
        return {
            'total_students': students.count(),
            'total_sessions': total_sessions,
            'attendance_threshold': self.attendance_threshold,
            'students': attendance_data,
            'average_attendance': (
                sum(d['attendance_percentage'] for d in attendance_data) / len(attendance_data)
            ) if attendance_data else 0
        }


class QRCode(models.Model):
    """
    Represents a QR code generated for a specific attendance session.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    qr_code = models.CharField(_('QR code'), max_length=255, unique=True)
    
    # Relationships
    module = models.ForeignKey(
        Module,
        on_delete=models.CASCADE,
        related_name='qrcodes',
        verbose_name=_('module')
    )
    lecturer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_qrcodes',
        verbose_name=_('lecturer'),
        limit_choices_to={'is_staff': True}
    )
    
    # Session details
    session_date = models.DateTimeField(_('session date'), default=timezone.now)
    expiration_minutes = models.PositiveSmallIntegerField(
        _('expiration (minutes)'),
        default=30,
        help_text=_('Number of minutes until the QR code expires')
    )
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('QR code')
        verbose_name_plural = _('QR codes')
        ordering = ['-session_date']
        indexes = [
            models.Index(fields=['is_active', 'session_date']),
            models.Index(fields=['module', 'session_date']),
        ]
    
    def __str__(self):
        return f"{self.module.code} - {self.session_date.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """
        Validate the model before saving.
        """
        super().clean()
        
        # Ensure the lecturer is assigned to the module
        if self.lecturer_id and not self.module.lecturers.filter(pk=self.lecturer_id).exists():
            raise ValidationError({
                'lecturer': _('The selected lecturer is not assigned to this module.')
            })
    
    def save(self, *args, **kwargs):
        """
        Save the QR code instance with additional processing.
        """
        self.full_clean()
        
        # Generate QR code data if not provided
        if not self.qr_code:
            import qrcode
            from io import BytesIO
            import base64
            
            # Create a unique identifier for this QR code
            qr_data = f"SMARTSCHOOL-{self.module_id}-{timezone.now().timestamp()}-{uuid.uuid4()}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Save QR code data
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            self.qr_code = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """
        Check if the QR code has expired.
        """
        expiration_time = self.session_date + timezone.timedelta(minutes=self.expiration_minutes)
        return timezone.now() > expiration_time
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('view_qr', kwargs={'qr_id': self.pk})


class Attendance(models.Model):
    """
    Represents a student's attendance record for a specific QR code session.
    """
    ATTENDANCE_STATUS = [
        ('PRESENT', _('Present')),
        ('LATE', _('Late')),
        ('ABSENT', _('Absent')),
        ('EXCUSED', _('Excused')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relationships
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_('student'),
        limit_choices_to={'is_staff': False}
    )
    qrcode = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        related_name='attendance_records',
        verbose_name=_('QR code')
    )
    
    # Attendance details
    status = models.CharField(
        _('status'),
        max_length=10,
        choices=ATTENDANCE_STATUS,
        default='PRESENT'
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    notes = models.TextField(_('notes'), blank=True)
    
    # Metadata
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('attendance record')
        verbose_name_plural = _('attendance records')
        ordering = ['-timestamp']
        unique_together = ['student', 'qrcode']
        indexes = [
            models.Index(fields=['student', 'qrcode']),
            models.Index(fields=['status', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.qrcode} - {self.get_status_display()}"
    
    def clean(self):
        """
        Validate the model before saving.
        """
        super().clean()
        
        # Ensure the student is enrolled in the module
        if self.student_id and self.qrcode_id:
            if not self.qrcode.module.students.filter(pk=self.student_id).exists():
                raise ValidationError({
                    'student': _('The selected student is not enrolled in this module.')
                })
    
    def save(self, *args, **kwargs):
        """
        Save the attendance record with additional processing.
        """
        self.full_clean()
        
        # Update timestamp if status changes
        if self.pk:
            old_instance = Attendance.objects.get(pk=self.pk)
            if old_instance.status != self.status:
                self.timestamp = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def is_on_time(self):
        """
        Check if the student was on time for the session.
        """
        if not self.qrcode or not self.timestamp:
            return False
            
        session_start = self.qrcode.session_date
        session_end = session_start + timezone.timedelta(minutes=self.qrcode.expiration_minutes)
        
        return session_start <= self.timestamp <= session_end
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('attendance_detail', kwargs={'pk': self.pk})
