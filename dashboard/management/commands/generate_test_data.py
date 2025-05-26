import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from attendance.models import Module, QRCode, Attendance
from dashboard.models import ClassSchedule

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test data for SmartSchool system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of test data (deletes existing test data)',
        )

    def handle(self, *args, **options):
        force = options['force']
        self.stdout.write('Generating test data...')
        
        # Check if test data already exists
        if not force and User.objects.filter(username__startswith='lecturer').exists():
            self.stdout.write(self.style.WARNING('Test data already exists. Use --force to recreate.'))
            return
        
        # Delete existing test data if force is True
        if force:
            self.stdout.write('Deleting existing test data...')
            User.objects.filter(username__startswith='lecturer').delete()
            User.objects.filter(username__startswith='student').delete()
            Module.objects.all().delete()
            ClassSchedule.objects.all().delete()
            QRCode.objects.all().delete()
            Attendance.objects.all().delete()
        
        # Create test users
        lecturer, created = User.objects.get_or_create(
            username='lecturer1',
            defaults={
                'email': 'lecturer1@smartschool.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'is_lecturer': True
            }
        )
        if created:
            lecturer.set_password('testpass123')
            lecturer.save()
        
        # Create students
        students = []
        for i in range(1, 21):
            username = f'student{i}'
            email = f'student{i}@smartschool.com'
            try:
                student = User.objects.get(username=username)
                if force:
                    student.email = email
                    student.first_name = f'Student{i}'
                    student.last_name = f'Lastname{i}'
                    student.is_student = True
                    student.set_password('testpass123')
                    student.save()
            except User.DoesNotExist:
                student = User.objects.create_user(
                    username=username,
                    email=email,
                    password='testpass123',
                    first_name=f'Student{i}',
                    last_name=f'Lastname{i}',
                    is_student=True
                )
            students.append(student)
        
        # Create or get modules
        modules_data = [
            {'code': 'CS101', 'name': 'Introduction to Programming'},
            {'code': 'CS201', 'name': 'Data Structures'},
            {'code': 'CS301', 'name': 'Algorithms'},
            {'code': 'CS401', 'name': 'Web Development'},
            {'code': 'CS501', 'name': 'Machine Learning'},
        ]
        
        modules = []
        for data in modules_data:
            module, created = Module.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'attendance_threshold': 75.00
                }
            )
            # Add lecturer to the module if not already added
            if lecturer not in module.lecturers.all():
                module.lecturers.add(lecturer)
            
            # Add random students to the module (10-20 students per module)
            if force or not module.students.exists():
                num_students = random.randint(10, min(20, len(students)))
                module.students.set(random.sample(students, num_students))
            
            modules.append(module)
        
        # Create class schedules for each module
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        time_slots = [
            ('09:00', '10:30'),
            ('11:00', '12:30'),
            ('14:00', '15:30'),
            ('16:00', '17:30')
        ]
        
        # Track scheduled times for each lecturer to avoid conflicts
        scheduled_slots = {}
        
        for module in modules:
            # Create 2 class schedules per week for each module
            for _ in range(2):
                max_attempts = 10  # Prevent infinite loops
                attempts = 0
                scheduled = False
                
                while not scheduled and attempts < max_attempts:
                    attempts += 1
                    day = random.choice(days)
                    start_time, end_time = random.choice(time_slots)
                    
                    # Check if lecturer already has a class at this time
                    conflict = False
                    if day in scheduled_slots.get(lecturer.id, {}):
                        for slot in scheduled_slots[lecturer.id][day]:
                            # Check for time overlap
                            if (start_time < slot[1] and end_time > slot[0]):
                                conflict = True
                                break
                    
                    if not conflict:
                        try:
                            # Create the schedule
                            schedule = ClassSchedule(
                                module=module,
                                lecturer=lecturer,
                                day_of_week=day,
                                start_time=start_time,
                                end_time=end_time,
                                room=f'Room {random.randint(1, 20)}',
                                is_active=True
                            )
                            schedule.full_clean()  # Validate before saving
                            schedule.save()
                            
                            # Track this time slot
                            if lecturer.id not in scheduled_slots:
                                scheduled_slots[lecturer.id] = {}
                            if day not in scheduled_slots[lecturer.id]:
                                scheduled_slots[lecturer.id][day] = []
                            scheduled_slots[lecturer.id][day].append((start_time, end_time))
                            scheduled = True
                            
                        except Exception as e:
                            # If validation fails, try another time slot
                            self.stdout.write(self.style.WARNING(f'Schedule conflict: {e}'))
                            continue
                    
                if not scheduled and attempts >= max_attempts:
                    self.stdout.write(self.style.WARNING(f'Could not schedule all classes for {module.code} - too many conflicts'))
        
        # Generate QR codes and attendance for the past 4 weeks
        now = timezone.now()
        for week in range(4):
            for day in range(5):  # Weekdays
                current_date = now - timedelta(weeks=4-week, days=now.weekday()-day)
                if current_date >= now:
                    continue
                
                for module in modules:
                    # 70% chance of having a session on this day
                    if random.random() < 0.7:
                        # Create a QR code for this session
                        session_time = current_date.replace(hour=random.randint(9, 15), minute=0, second=0, microsecond=0)
                        qr = QRCode.objects.create(
                            module=module,
                            lecturer=lecturer,
                            session_date=session_time,
                            is_active=False,
                            expiration_minutes=120
                        )
                        qr.generate_qr_image()
                        qr.save()
                        
                        # Generate attendance for each student in this module
                        for student in module.students.all():
                            # 80% chance of being present, 10% late, 10% absent
                            status_roll = random.random()
                            if status_roll < 0.8:  # 80% present
                                status = 'present'
                                scan_time = session_time + timedelta(minutes=random.randint(0, 30))
                            elif status_roll < 0.9:  # 10% late
                                status = 'present'  # Still marked as present but with late scan
                                scan_time = session_time + timedelta(minutes=random.randint(31, 120))
                            else:  # 10% absent
                                status = 'absent'
                                scan_time = None
                            
                            if status != 'absent':
                                # Create attendance record
                                Attendance.objects.create(
                                    student=student,
                                    qrcode=qr,
                                    timestamp=scan_time,
                                    status=status,
                                    biometric_verified=random.choice([True, False])
                                )
        
        self.stdout.write(self.style.SUCCESS('Successfully generated test data!'))
        self.stdout.write(self.style.SUCCESS(f'Created {User.objects.count()} users'))
        self.stdout.write(self.style.SUCCESS(f'Created {Module.objects.count()} modules'))
        self.stdout.write(self.style.SUCCESS(f'Created {ClassSchedule.objects.count()} class schedules'))
        self.stdout.write(self.style.SUCCESS(f'Created {QRCode.objects.count()} QR codes'))
        self.stdout.write(self.style.SUCCESS(f'Created {Attendance.objects.count()} attendance records'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write(f'Lecturer: username=lecturer1, password=testpass123')
        self.stdout.write(f'Students: username=student1..20, password=testpass123')
