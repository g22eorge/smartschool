"""
This module contains all the models for the SmartSchool attendance system.
"""
# Import core models
from .core import Module, QRCode, Attendance

# Import user-related models
from .user import User, UserSession

# Make models available at the package level
__all__ = [
    'User',
    'UserSession',
    'Module',
    'QRCode',
    'Attendance',
]
