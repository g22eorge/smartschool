#!/usr/bin/env python
"""
Standalone script to populate the database with test data.
Run with: python populate_test_data.py
"""
import os
import sys
import random
import uuid
from datetime import datetime, time, timedelta

def run():
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_auth.settings')
    import django
    django.setup()
    
    from django.contrib.auth import get_user_model
    from django.utils import timezone
    from django.db import transaction
    
    # Import models using Django's app registry
    from django.apps import apps
    
    # Get models
    User = get_user_model()
    Module = apps.get_model('attendance', 'Module')
    QRCode = apps.get_model('attendance', 'QRCode')
    Attendance = apps.get_model('attendance', 'Attendance')
    ClassSchedule = apps.get_model('dashboard', 'ClassSchedule')
    
    print("Starting to populate database with test data...")
    
    with transaction.atomic():
        # Create admin user
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
            print("Created admin user")
        
        # Create 10 lecturers
        print("Creating lecturers...")
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
        print(f"Created {len(lecturers)} lecturers")
        
        # Create 100 students
        print("Creating students...")
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
        print(f"Created {len(students)} students")
        
        # Create modules
        print("Creating modules...")
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
                }
            )
            modules.append(module)
        print(f"Created {len(modules)} modules")
        
        # Enroll students in modules
        print("Enrolling students in modules...")
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
        
        print("Enrollment complete")
        
        # Create class schedules
        print("Creating class schedules...")
        days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        time_slots = [
            (time(8, 0), time(9, 30)),    # 8:00 - 9:30
            (time(9, 30), time(11, 0)),   # 9:30 - 11:00
            (time(11, 0), time(12, 30)),  # 11:00 - 12:30
            (time(13, 0), time(14, 30)),  # 1:00 - 2:30
            (time(14, 30), time(16, 0)),  # 2:30 - 4:00
            (time(16, 0), time(17, 30))   # 4:00 - 5:30
        ]
        
        # Create a list to track lecturer availability
        lecturer_availability = {}
        for lecturer in lecturers:
            lecturer_availability[lecturer.id] = {day: [] for day in days_of_week}
        
        for module in modules:
            # Each module has 1-3 class sessions per week
            num_sessions = random.randint(1, 3)
            
            for _ in range(num_sessions):
                day = random.choice(days_of_week)
                
                # Find an available lecturer and time slot
                available = False
                for _ in range(10):  # Try up to 10 times to find an available slot
                    lecturer = random.choice(lecturers)
                    available_slots = [slot for slot in time_slots 
                                     if slot not in lecturer_availability[lecturer.id][day]]
                    
                    if available_slots:
                        time_slot = random.choice(available_slots)
                        lecturer_availability[lecturer.id][day].append(time_slot)
                        available = True
                        break
                
                if not available:
                    print(f"Warning: Could not find available slot for {module.code}. Skipping...")
                    continue
                
                start_time, end_time = time_slot
                
                # Create the class schedule
                try:
                    ClassSchedule.objects.create(
                        module=module,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time,
                        room=f'Room {random.randint(100, 500)}-{chr(65 + random.randint(0, 25))}',
                        lecturer=lecturer,
                        is_active=True
                    )
                except Exception as e:
                    print(f"Error creating schedule for {module.code}: {str(e)}")
        
        print("Class schedules created")
        
        # Create attendance sessions with QR codes
        print("Creating attendance sessions...")
        today = timezone.now()
        
        # Create past sessions (2-4 per module)
        for module in modules:
            num_sessions = random.randint(2, 4)
            for i in range(num_sessions):
                # Create a session in the past (1-30 days ago)
                session_date = today - timedelta(days=random.randint(1, 30))
                
                # Create the QR code with a unique code
                qr_code = QRCode(
                    module=module,
                    lecturer=random.choice(lecturers),
                    session_date=session_date,
                    is_active=False,
                    expiration_minutes=60,  # 1 hour session
                    qr_code=f"QR-{module.code}-{session_date.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
                )
                qr_code.save()  # This will trigger the signal handler
                
                # Generate QR code image
                qr_code.generate_qr_image()
                qr_code.save()
                
                # Create attendance records for 70-90% of students
                for student in module.students.all():
                    if random.random() < random.uniform(0.7, 0.9):  # 70-90% chance of being present
                        Attendance.objects.create(
                            student=student,
                            qrcode=qr_code,
                            timestamp=session_date + timedelta(minutes=random.randint(1, 30)),
                            status='present'
                        )
            
            # Create 1-2 upcoming sessions per module
            for _ in range(random.randint(1, 2)):
                # Session starts in 1-7 days
                session_date = today + timedelta(days=random.randint(1, 7))
                
                # Create the QR code for future session with a unique code
                qr_code = QRCode(
                    module=module,
                    lecturer=random.choice(lecturers),
                    session_date=session_date,
                    is_active=False,
                    expiration_minutes=60,
                    qr_code=f"QR-{module.code}-{session_date.strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
                )
                qr_code.save()  # This will trigger the signal handler
                
                # Generate QR code image
                qr_code.generate_qr_image()
                qr_code.save()
        
        print("Attendance sessions created")
    
    print("\nTest data population complete!")
    print("\nYou can now log in with these test accounts:")
    print("Admin: admin / admin123")
    print("Lecturers: lecturer1-10 / lecturer123")
    print("Students: student1-100 / student123")

if __name__ == '__main__':
    run()
