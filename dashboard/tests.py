from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import User
from attendance.models import Module, QRCode, Attendance
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()

class DashboardViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a lecturer user
        self.lecturer = User.objects.create_user(
            username='lecturer1',
            email='lecturer@example.com',
            password='testpass123',
            is_lecturer=True
        )
        
        # Create a student user
        self.student = User.objects.create_user(
            username='student1',
            email='student@example.com',
            password='testpass123',
            is_student=True
        )
        
        # Create a module
        self.module = Module.objects.create(
            code='CS101',
            name='Introduction to Computer Science',
            description='Basic concepts of computer science',
            course_outline='Week 1: Introduction\nWeek 2: Basic Concepts',
            attendance_threshold=75.00
        )
        self.module.lecturers.add(self.lecturer)
        self.module.students.add(self.student)
        
        # Create a QR code for attendance
        self.qr_code = QRCode.objects.create(
            module=self.module,
            lecturer=self.lecturer,
            session_date=timezone.now() - timedelta(days=1),
            expiration_minutes=60,
            is_active=False
        )
        
        # Create an attendance record
        self.attendance = Attendance.objects.create(
            student=self.student,
            qrcode=self.qr_code,
            status='present',
            timestamp=timezone.now() - timedelta(days=1)
        )
    
    def test_dashboard_redirects_anonymous_user(self):
        """Test that anonymous users are redirected to login"""
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/attendance/login/', response.url)
    
    def test_student_dashboard_access(self):
        """Test that student can access their dashboard"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('dashboard:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/student.html')
    
    def test_lecturer_dashboard_access(self):
        """Test that lecturer can access their dashboard"""
        self.client.login(username='lecturer1', password='testpass123')
        response = self.client.get(reverse('dashboard:lecturer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/lecturer.html')
    
    def test_student_can_view_attendance(self):
        """Test that student can view their attendance"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('dashboard:attendance_records'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'dashboard/student_attendance.html')
        # Check if the attendance record is in the context
        self.assertIn('attendance_by_module', response.context)
        # The attendance_by_module is a dict with module IDs as keys
        self.assertIn(self.module.id, response.context['attendance_by_module'])
    
    def test_lecturer_can_view_module_attendance(self):
        """Test that lecturer can view attendance for their module"""
        self.client.login(username='lecturer1', password='testpass123')
        # Using the attendance_stats view which shows module attendance
        response = self.client.get(reverse('dashboard:attendance_stats'))
        self.assertEqual(response.status_code, 200)
        # Check if the module stats are in the context
        self.assertIn('module_stats', response.context)
        # Check if our test module is in the module_stats
        module_codes = [m['code'] for m in response.context['module_stats']]
        self.assertIn(self.module.code, module_codes)
