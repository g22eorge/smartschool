from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from attendance.models import Module, QRCode, Attendance
from dashboard.models import ClassSchedule
from datetime import time, timedelta
import random
from faker import Faker

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test data for the schedule module'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreation of schedule data (deletes existing schedules)',
        )

    def handle(self, *args, **options):
        fake = Faker()
        force = options['force']
        
        if force:
            self.stdout.write('Deleting existing schedule data...')
            ClassSchedule.objects.all().delete()
        
        # Get or create a lecturer
        lecturer, _ = User.objects.get_or_create(
            username='schedule_lecturer',
            defaults={
                'email': 'lecturer@schedule.com',
                'first_name': 'Schedule',
                'last_name': 'Professor',
                'is_lecturer': True
            }
        )
        if _:
            lecturer.set_password('testpass123')
            lecturer.save()
        
        # Create test modules if they don't exist
        modules_data = [
            {'code': 'CS401', 'name': 'Web Development'},
            {'code': 'CS402', 'name': 'Mobile App Development'},
            {'code': 'CS403', 'name': 'Cloud Computing'},
            {'code': 'CS404', 'name': 'Data Science'},
            {'code': 'CS405', 'name': 'Cyber Security'},
        ]
        
        modules = []
        for data in modules_data:
            module, _ = Module.objects.get_or_create(
                code=data['code'],
                defaults={
                    'name': data['name'],
                    'attendance_threshold': 75.00
                }
            )
            module.lecturers.add(lecturer)
            modules.append(module)
        
        # Create class schedules
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        time_slots = [
            ('09:00', '10:30'),
            ('11:00', '12:30'),
            ('14:00', '15:30'),
            ('16:00', '17:30'),
        ]
        
        room_numbers = [f"R{100 + i}" for i in range(1, 21)]
        
        # Track scheduled times to avoid conflicts
        scheduled_slots = {}
        
        for module in modules:
            # Create 2-3 class schedules per module
            for _ in range(random.randint(2, 3)):
                max_attempts = 10
                attempts = 0
                scheduled = False
                
                while not scheduled and attempts < max_attempts:
                    attempts += 1
                    day = random.choice(days)
                    start_time_str, end_time_str = random.choice(time_slots)
                    start_time = time(*map(int, start_time_str.split(':')))
                    end_time = time(*map(int, end_time_str.split(':')))
                    room = random.choice(room_numbers)
                    
                    # Check for conflicts
                    conflict = False
                    if day in scheduled_slots.get(lecturer.id, {}):
                        for slot in scheduled_slots[lecturer.id][day]:
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
                                start_time=start_time_str,
                                end_time=end_time_str,
                                room=room,
                                is_active=True
                            )
                            schedule.full_clean()
                            schedule.save()
                            
                            # Track this time slot
                            if lecturer.id not in scheduled_slots:
                                scheduled_slots[lecturer.id] = {}
                            if day not in scheduled_slots[lecturer.id]:
                                scheduled_slots[lecturer.id][day] = []
                            scheduled_slots[lecturer.id][day].append((start_time, end_time))
                            scheduled = True
                            
                            self.stdout.write(self.style.SUCCESS(
                                f'Created schedule: {module.code} on {day} {start_time_str}-{end_time_str} in {room}'
                            ))
                            
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f'Error creating schedule: {e}'))
                            continue
                    
                    if not scheduled and attempts >= max_attempts:
                        self.stdout.write(self.style.WARNING(
                            f'Could not schedule all classes for {module.code} - too many conflicts'
                        ))
        
        self.stdout.write(self.style.SUCCESS('\nSuccessfully generated schedule data!'))
        self.stdout.write(f'Lecturer credentials: username=schedule_lecturer, password=testpass123')
        self.stdout.write('You can now log in and view the schedule at /dashboard/lecturer/')
