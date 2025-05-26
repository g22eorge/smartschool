import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_auth.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_superuser():
    User = get_user_model()
    
    # New superuser credentials
    username = 'admin2'
    email = 'admin2@smartschool.com'
    password = 'admin123'  # In production, use a stronger password
    
    # Check if user already exists
    if not User.objects.filter(username=username).exists():
        print("Creating new superuser...")
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print("Superuser created successfully!")
        print(f"Username: {username}")
        print(f"Password: {password}")
    else:
        print("Superuser already exists.")
        print("If you forgot the password, you can change it in the admin panel.")

if __name__ == "__main__":
    create_superuser()
