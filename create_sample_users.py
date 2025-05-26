import os
import django

def create_sample_users():
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_auth.settings')
    django.setup()
    
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group
    
    User = get_user_model()
    
    # Create groups if they don't exist
    lecturer_group, _ = Group.objects.get_or_create(name='Lecturer')
    student_group, _ = Group.objects.get_or_create(name='Student')
    
    # Sample users data
    users = [
        # Lecturers
        {
            'username': 'jdoe',
            'email': 'john.doe@university.edu',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'lecturer123',
            'is_staff': True,
            'groups': [lecturer_group],
        },
        {
            'username': 'asmith',
            'email': 'alice.smith@university.edu',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'password': 'lecturer123',
            'is_staff': True,
            'groups': [lecturer_group],
        },
        
        # Students
        {
            'username': 'student1',
            'email': 'student1@university.edu',
            'first_name': 'Michael',
            'last_name': 'Johnson',
            'password': 'student123',
            'groups': [student_group],
        },
        {
            'username': 'student2',
            'email': 'student2@university.edu',
            'first_name': 'Sarah',
            'last_name': 'Williams',
            'password': 'student123',
            'groups': [student_group],
        },
        {
            'username': 'student3',
            'email': 'student3@university.edu',
            'first_name': 'David',
            'last_name': 'Brown',
            'password': 'student123',
            'groups': [student_group],
        },
    ]
    
    created_count = 0
    
    for user_data in users:
        username = user_data.pop('username')
        password = user_data.pop('password')
        groups = user_data.pop('groups', [])
        
        # Check if user already exists
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password=password,
                **user_data
            )
            
            # Add user to groups
            for group in groups:
                user.groups.add(group)
            
            created_count += 1
            print(f"Created user: {username}")
        else:
            print(f"User {username} already exists, skipping...")
    
    print(f"\nSuccessfully created {created_count} new users.")

if __name__ == "__main__":
    create_sample_users()
