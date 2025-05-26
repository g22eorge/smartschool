from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from attendance.models import QRCode, Attendance, Module, Student
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Generate dummy attendance data for testing the 30-Day Attendance Trend chart'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get or create a test lecturer
        lecturer, _ = User.objects.get_or_create(
            username='test_lecturer',
            defaults={
                'first_name': 'Test',
                'last_name': 'Lecturer',
                'email': 'lecturer@example.com',
                'is_staff': True,
                'is_active': True
            }
        )
        
        # Get or create a test module
        module, _ = Module.objects.get_or_create(
            code='CS101',
            defaults={
                'name': 'Introduction to Computer Science',
                'description': 'Test module for dummy data'
            }
        )
        
        # Add lecturer to module if not already added
        if lecturer not in module.lecturers.all():
            module.lecturers.add(lecturer)
        
        # Create test students if they don't exist
        students = []
        for i in range(1, 26):  # 25 students
            student, _ = User.objects.get_or_create(
                username=f'student{i}',
                defaults={
                    'first_name': f'Student',
                    'last_name': str(i),
                    'email': f'student{i}@example.com',
                    'is_student': True,
                    'is_active': True
                }
            )
            # Create student profile if it doesn't exist
            Student.objects.get_or_create(user=student, student_id=f'STD{1000 + i}')
            students.append(student)
            
            # Add student to module if not already added
            if student not in module.students.all():
                module.students.add(student)
        
        # Generate attendance data for the past 30 days
        today = timezone.now().date()
        for day in range(30):
            date = today - timedelta(days=day)
            
            # Create a QR code for this session
            qr_code = QRCode.objects.create(
                module=module,
                lecturer=lecturer,
                session_date=date,
                is_active=False,  # Past sessions are not active
                duration_minutes=60
            )
            
            # Generate attendance records for each student
            for student in students:
                # 70-95% chance of being present
                is_present = random.random() > 0.15
                
                Attendance.objects.create(
                    qr_code=qr_code,
                    student=student.student_profile,
                    is_present=is_present,
                    timestamp=timezone.make_aware(
                        timezone.datetime.combine(date, timezone.now().time())
                    )
                )
            
            self.stdout.write(self.style.SUCCESS(f'Created attendance records for {date}'))
        
        self.stdout.write(self.style.SUCCESS('Successfully generated dummy attendance data!'))
