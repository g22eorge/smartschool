"""
Custom user model for the SmartSchool application.
"""
import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.conf import settings


class UserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifier
    for authentication instead of usernames.
    """
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier
    instead of username.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    first_name = models.CharField(_('first name'), max_length=150, blank=True)
    last_name = models.CharField(_('last name'), max_length=150, blank=True)
    
    # Authentication fields
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    last_login = models.DateTimeField(_('last login'), blank=True, null=True)
    login_count = models.PositiveIntegerField(_('login count'), default=0)
    
    # Additional fields
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pics/',
        blank=True,
        null=True
    )
    
    # User preferences
    language = models.CharField(
        _('language'),
        max_length=10,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE
    )
    timezone = models.CharField(
        _('timezone'),
        max_length=50,
        default=settings.TIME_ZONE
    )
    
    # Security
    email_verified = models.BooleanField(_('email verified'), default=False)
    two_factor_enabled = models.BooleanField(_('two factor enabled'), default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
    
    def increment_login_count(self):
        """Increment the login count for the user."""
        self.login_count = models.F('login_count') + 1
        self.save(update_fields=['login_count', 'last_login'])
    
    def clean(self):
        """
        Custom validation for the user model.
        """
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)
        
        # Validate email domain if needed
        allowed_domains = getattr(settings, 'ALLOWED_EMAIL_DOMAINS', None)
        if allowed_domains and '@' in self.email:
            domain = self.email.split('@')[1]
            if domain not in allowed_domains:
                raise ValidationError({
                    'email': _('Email domain not allowed.')
                })
    
    def save(self, *args, **kwargs):
        """
        Save the user instance with additional processing.
        """
        self.full_clean()
        super().save(*args, **kwargs)


class UserSession(models.Model):
    """
    Model to track user sessions for security and analytics.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name=_('user')
    )
    session_key = models.CharField(_('session key'), max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    device = models.CharField(_('device'), max_length=255, blank=True)
    browser = models.CharField(_('browser'), max_length=100, blank=True)
    os = models.CharField(_('operating system'), max_length=100, blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    expires_at = models.DateTimeField(_('expires at'))
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        verbose_name = _('user session')
        verbose_name_plural = _('user sessions')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.email} - {self.ip_address or 'Unknown IP'}"
    
    @classmethod
    def create_from_request(cls, request, user):
        """
        Create a new user session from a request.
        """
        from user_agents import parse
        
        session = request.session
        user_agent = parse(request.META.get('HTTP_USER_AGENT', ''))
        
        return cls.objects.create(
            user=user,
            session_key=session.session_key or '',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device=f"{user_agent.device.brand or ''} {user_agent.device.model or ''}".strip() or 'Unknown',
            browser=f"{user_agent.browser.family} {user_agent.browser.version_string}".strip(),
            os=f"{user_agent.os.family} {user_agent.os.version_string}".strip(),
            expires_at=session.get_expiry_date(),
        )
    
    def end_session(self):
        """
        Mark the session as inactive.
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'last_activity'])
        return True
