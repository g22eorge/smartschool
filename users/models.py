from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import UserManager


class User(AbstractUser):
    """
    Custom user model that extends the default Django User model.
    """
    # Remove username field and make email the unique identifier
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    # Additional fields
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    profile_picture = models.ImageField(
        _('profile picture'), 
        upload_to='profile_pics/', 
        null=True, 
        blank=True
    )
    bio = models.TextField(_('biography'), blank=True)
    
    # Role fields
    is_lecturer = models.BooleanField(
        _('lecturer status'),
        default=False,
        help_text=_('Designates whether the user is a lecturer.')
    )
    is_student = models.BooleanField(
        _('student status'),
        default=True,
        help_text=_('Designates whether the user is a student.')
    )
    
    # Set email as the USERNAME_FIELD for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Use custom UserManager
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.get_full_name() or self.email
