from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings

# Using string reference to avoid circular imports
@receiver(post_save, sender='users.User')
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to create a user profile when a new user is created.
    """
    if created:
        # Any additional setup when a new user is created can go here
        pass

@receiver(post_save, sender='users.User')
def save_user_profile(sender, instance, **kwargs):
    """
    Signal to save the user profile when the user is saved.
    """
    # Any additional actions when a user is saved can go here
    pass

def ready(app_config):
    """
    Connect signals when the app is ready.
    This function is called from apps.py
    """
    # Import here to avoid AppRegistryNotReady exception
    from django.db.models.signals import post_save
    from .models import User
    
    # Connect signals
    post_save.connect(create_user_profile, sender=User)
    post_save.connect(save_user_profile, sender=User)
