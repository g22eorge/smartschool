"""
Management command to populate the database with dummy data for testing and development.
"""
import random
from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
# Use absolute imports to avoid circular imports
from django.apps import apps

# Get models using the app registry
def get_model(model_name):
    if model_name in ['Module', 'QRCode', 'Attendance']:
        return apps.get_model('attendance', model_name)
    return apps.get_model('dashboard', model_name)

# Import models using the app registry
Module = get_model('Module')
QRCode = get_model('QRCode')
Attendance = get_model('Attendance')
ClassSchedule = get_model('ClassSchedule')
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with dummy data for testing and development.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to populate database with dummy data...'))
        
        try:
            with transaction.atomic():
                # Create test users
                self.stdout.write('Creating test users...')
                users = self.create_test_users()
                
                # Create test modules
                self.stdout.write('Creating test modules...')
                modules = self.create_test_modules()
                
                # Enroll students in modules
                self.stdout.write('Enrolling students in modules...')
                self.enroll_students_in_modules(users['students'], modules)
                
                # Create class schedules
                self.stdout.write('Creating class schedules...')
                self.create_class_schedules(modules, users['lecturers'])
                
                # Create attendance sessions
                self.stdout.write('Creating attendance sessions...')
                self.create_attendance_sessions(modules, users['lecturers'], users['students'])
                
                self.stdout.write(self.style.SUCCESS('Successfully populated database with dummy data!'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error populating database: {str(e)}'))
            raise
    
    def create_test_users(self):
        """Create test users (admin, lecturers, and students)."""
        # Create admin user if not exists
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@smartschool.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        # Create 10 lecturers
        lecturers = []
        lecturer_first_names = [
            'James', 'Mary', 'Robert', 'Patricia', 'John', 'Jennifer', 
            'Michael', 'Linda', 'David', 'Elizabeth'
        ]
        lecturer_last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 
            'Miller', 'Davis', 'Rodriguez', 'Martinez'
        ]
        
        for i in range(1, 11):
            first_name = lecturer_first_names[i-1]
            last_name = lecturer_last_names[i-1]
            username = f'lecturer{i}'
            email = f'{first_name.lower()}.{last_name.lower()}@smartschool.com'
            
            lecturer, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_lecturer': True,
                    'is_active': True,
                }
            )
            if created:
                lecturer.set_password('lecturer123')
                lecturer.save()
            lecturers.append(lecturer)
        
        # Create 100 students
        students = []
        student_first_names = [
            'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'William', 'Sophia', 'Elijah', 'Isabella', 'James',
            'Charlotte', 'Benjamin', 'Amelia', 'Lucas', 'Mia', 'Mason', 'Harper', 'Logan', 'Evelyn', 'Alexander',
            'Abigail', 'Ethan', 'Emily', 'Jacob', 'Elizabeth', 'Michael', 'Mila', 'Daniel', 'Ella', 'Henry',
            'Avery', 'Jackson', 'Sofia', 'Sebastian', 'Camila', 'Aiden', 'Aria', 'Matthew', 'Scarlett', 'Samuel',
            'Victoria', 'David', 'Madison', 'Joseph', 'Luna', 'Carter', 'Grace', 'Owen', 'Chloe', 'Wyatt', 'Penelope',
            'John', 'Layla', 'Jack', 'Riley', 'Luke', 'Zoey', 'Jayden', 'Nora', 'Dylan', 'Lily',
            'Grayson', 'Eleanor', 'Levi', 'Hannah', 'Isaac', 'Lillian', 'Gabriel', 'Addison', 'Julian', 'Aubrey',
            'Mateo', 'Ellie', 'Anthony', 'Stella', 'Jaxon', 'Natalie', 'Lincoln', 'Zoe', 'Joshua', 'Leah',
            'Christopher', 'Hazel', 'Andrew', 'Violet', 'Theodore', 'Aurora', 'Caleb', 'Savannah', 'Ryan', 'Audrey',
            'Asher', 'Brooklyn', 'Nathan', 'Bella', 'Thomas', 'Claire', 'Leo', 'Skylar', 'Isaiah', 'Lucy',
            'Charles', 'Paisley', 'Josiah', 'Everly', 'Hudson', 'Anna', 'Christian', 'Caroline', 'Hunter', 'Nova'
        ]
        
        for i in range(1, 101):
            first_name = student_first_names[i-1] if i <= len(student_first_names) else f'Student{i}'
            last_name = f'Student{i}'
            username = f'student{i}'
            email = f'student{i}@smartschool.com'
            
            student, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_student': True,
                    'is_active': True,
                }
            )
            if created:
                student.set_password('student123')
                student.save()
            students.append(student)
        
        return {
            'admin': admin,
            'lecturers': lecturers,
            'students': students,
        }
    
    def create_test_modules(self):
        """Create test modules."""
        modules = []
        module_data = [
            # Core CS modules
            {'code': 'CS401', 'name': 'Web Development', 'description': 'Introduction to modern web development'},
            {'code': 'CS402', 'name': 'Database Systems', 'description': 'Fundamentals of database design and implementation'},
            {'code': 'CS403', 'name': 'Algorithms', 'description': 'Advanced algorithms and data structures'},
            {'code': 'CS404', 'name': 'Machine Learning', 'description': 'Introduction to machine learning concepts'},
            {'code': 'CS405', 'name': 'Mobile App Development', 'description': 'Building mobile applications'},
            
            # Additional modules
            {'code': 'CS406', 'name': 'Computer Networks', 'description': 'Fundamentals of computer networking'},
            {'code': 'CS407', 'name': 'Software Engineering', 'description': 'Software development methodologies and practices'},
            {'code': 'CS408', 'name': 'Cybersecurity', 'description': 'Principles of information security'},
            {'code': 'CS409', 'name': 'Cloud Computing', 'description': 'Cloud infrastructure and services'},
            {'code': 'CS410', 'name': 'Data Science', 'description': 'Data analysis and visualization'},
            
            # Electives
            {'code': 'CS411', 'name': 'Game Development', 'description': 'Principles of game design and development'},
            {'code': 'CS412', 'name': 'IoT Systems', 'description': 'Internet of Things architecture and applications'},
            {'code': 'CS413', 'name': 'Blockchain Technology', 'description': 'Distributed ledger technology'},
            {'code': 'CS414', 'name': 'Computer Graphics', 'description': '2D and 3D computer graphics'},
            {'code': 'CS415', 'name': 'Natural Language Processing', 'description': 'Processing and analyzing human language data'},
        ]
        
        for data in module_data:
            module, created = Module.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'description': data['description'],
                    'credits': 15,
                }
            )
            modules.append(module)
        
        return modules
    
    def enroll_students_in_modules(self, students, modules):
        """Enroll students in modules."""
        # Ensure each student is enrolled in 4-6 modules
        for student in students:
            # Each student takes 4-6 random modules
            num_modules = random.randint(4, 6)
            student_modules = random.sample(modules, min(num_modules, len(modules)))
            for module in student_modules:
                module.students.add(student)
        
        # Ensure each module has at least 10 students
        for module in modules:
            if module.students.count() < 10:
                # Get students not already in this module
                available_students = [s for s in students if s not in module.students.all()]
                if available_students:
                    # Add enough students to reach at least 10
                    needed = 10 - module.students.count()
                    module.students.add(*random.sample(available_students, min(needed, len(available_students))))
    
    def create_class_schedules(self, modules, lecturers):
        """Create class schedules for modules."""
        weekdays = [
            ClassSchedule.MONDAY,
            ClassSchedule.TUESDAY,
            ClassSchedule.WEDNESDAY,
            ClassSchedule.THURSDAY,
            ClassSchedule.FRIDAY,
        ]
        
        time_slots = [
            {'start': time(9, 0), 'end': time(10, 30)},
            {'start': time(11, 0), 'end': time(12, 30)},
            {'start': time(14, 0), 'end': time(15, 30)},
            {'start': time(16, 0), 'end': time(17, 30)},
        ]
        
        for module in modules:
            # Each module has 1-2 class sessions per week
            num_sessions = random.randint(1, 2)
            selected_slots = random.sample(time_slots, min(num_sessions, len(time_slots)))
            
            for slot in selected_slots:
                ClassSchedule.objects.get_or_create(
                    module=module,
                    day_of_week=random.choice(weekdays),
                    start_time=slot['start'],
                    end_time=slot['end'],
                    defaults={
                        'room': f'Room {random.randint(100, 500)}',
                        'lecturer': random.choice(lecturers),
                    }
                )
    
    def create_attendance_sessions(self, modules, lecturers, students):
        """Create past and future attendance sessions with attendance records."""
        today = timezone.now().date()
        
        for module in modules:
            # Create 3-5 past sessions for each module
            num_past_sessions = random.randint(3, 5)
            
            # Create past sessions (completed)
            for i in range(num_past_sessions):
                # Create a session in the past (1-30 days ago)
                session_date = today - timedelta(days=random.randint(1, 30))
                start_time = timezone.make_aware(datetime.combine(session_date, time(random.randint(8, 16), random.choice([0, 30]))))
                end_time = start_time + timedelta(hours=1, minutes=30)
                
                # Create QR code for the session
                qr_code = QRCode.objects.create(
                    module=module,
                    lecturer=random.choice(lecturers),
                    start_time=start_time,
                    end_time=end_time,
                    is_active=False,  # Past sessions are not active
                    location=f'Room {random.randint(100, 500)}-{chr(65 + random.randint(0, 25))}',
                )
                
                # Create attendance records for students enrolled in this module
                module_students = list(module.students.all())
                
                for student in module_students:
                    # 70-90% chance of being present for past sessions
                    is_present = random.random() < random.uniform(0.7, 0.9)
                    
                    Attendance.objects.create(
                        student=student,
                        qr_code=qr_code,
                        is_present=is_present,
                        timestamp=start_time + timedelta(minutes=random.randint(0, 30)),
                    )
            
            # Create 1-2 active sessions (happening now)
            for _ in range(random.randint(1, 2)):
                # Session started 0-30 minutes ago and ends in 30-90 minutes
                start_time = timezone.now() - timedelta(minutes=random.randint(0, 30))
                end_time = start_time + timedelta(minutes=random.randint(30, 90))
                
                qr_code = QRCode.objects.create(
                    module=module,
                    lecturer=random.choice(lecturers),
                    start_time=start_time,
                    end_time=end_time,
                    is_active=True,  # Currently active session
                    location=f'Room {random.randint(100, 500)}-{chr(65 + random.randint(0, 25))}',
                )
                
                # Some students have already checked in (30-70% of the class)
                module_students = list(module.students.all())
                num_present = int(len(module_students) * random.uniform(0.3, 0.7))
                
                for student in random.sample(module_students, num_present):
                    Attendance.objects.create(
                        student=student,
                        qr_code=qr_code,
                        is_present=True,
                        timestamp=start_time + timedelta(minutes=random.randint(0, int((timezone.now() - start_time).total_seconds() / 60))),
                    )
            
            # Create 1-2 upcoming sessions (in the future)
            for _ in range(random.randint(1, 2)):
                # Session starts in 1-7 days
                session_date = today + timedelta(days=random.randint(1, 7))
                start_time = timezone.make_aware(datetime.combine(session_date, time(random.randint(8, 16), random.choice([0, 30]))))
                end_time = start_time + timedelta(hours=1, minutes=30)
                
                QRCode.objects.create(
                    module=module,
                    lecturer=random.choice(lecturers),
                    start_time=start_time,
                    end_time=end_time,
                    is_active=False,  # Not active yet
                    location=f'Room {random.randint(100, 500)}-{chr(65 + random.randint(0, 25))}',
                )
