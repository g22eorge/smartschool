import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

# Set up logging
logger = logging.getLogger(__name__)

User = get_user_model()

class CustomAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        print(f"\n=== AUTHENTICATE START ===")
        print(f"Username: {username}")
        print(f"Request: {request}")
        print(f"Session key: {getattr(request, 'session', {}).session_key}")
        
        if not username or not password:
            print("Username or password not provided")
            return None
            
        try:
            print(f"Looking up user: {username}")
            user = User.objects.get(username=username)
            print(f"Found user: {user.id} - {user.username}")
            print(f"User is active: {user.is_active}")
            print(f"User is staff: {user.is_staff}")
            print(f"User is superuser: {user.is_superuser}")
            
            # Check password
            if user.check_password(password):
                print("Password is valid")
                # Check if the user should be able to authenticate
                if self.user_can_authenticate(user):
                    print("User can authenticate")
                    return user
                else:
                    print("User cannot authenticate (inactive or not allowed)")
            else:
                print("Invalid password")
                
        except User.DoesNotExist:
            print(f"User {username} does not exist")
        except Exception as e:
            print(f"Error during authentication: {str(e)}")
            
        print("Authentication failed")
        return None

    def get_user(self, user_id):
        print(f"\n=== GET USER ===")
        print(f"User ID: {user_id}")
        try:
            user = User.objects.get(pk=user_id)
            print(f"Found user: {user.username}")
            print(f"User is active: {user.is_active}")
            return user if self.user_can_authenticate(user) else None
        except User.DoesNotExist:
            print(f"User with ID {user_id} does not exist")
            return None
