from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.backends.base import UpdateError
from django.core.exceptions import SuspiciousOperation
import json

class SessionRefreshMiddleware:
    """
    Middleware to ensure the session is saved after every request.
    This helps prevent session-related redirect loops.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request and get the response
        response = self.get_response(request)
        
        # Ensure the session is saved if it has been modified
        if hasattr(request, 'session') and request.session.modified:
            try:
                request.session.save()
            except (UpdateError, SuspiciousOperation) as e:
                # Log the error but don't break the request
                print(f"Session save error: {e}")
                pass
            
        return response


class MultipleSessionsMiddleware:
    """
    Middleware to support multiple concurrent sessions for different roles.
    This allows users to be logged in as different roles in different tabs/windows.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Generate a unique session key for this role
        if request.user.is_authenticated:
            role = self._get_user_role(request.user)
            if role:
                # Create a role-specific session key
                role_key = f"{request.session.session_key}_{role}"
                if not request.session.get('role_key') or request.session.get('role_key') != role_key:
                    # Update the session with the role key
                    request.session['role_key'] = role_key
                    request.session['user_role'] = role
                    request.session.save()
        
        response = self.get_response(request)
        return response
    
    def _get_user_role(self, user):
        """Determine the user's primary role."""
        if user.is_superuser:
            return 'admin'
        elif hasattr(user, 'is_lecturer') and user.is_lecturer:
            return 'lecturer'
        elif hasattr(user, 'is_student') and user.is_student:
            return 'student'
        return None


class RoleBasedSessionMiddleware:
    """
    Middleware to handle role-based session data isolation.
    This ensures that session data is properly scoped to the current role.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request and get response
        response = self.get_response(request)
        
        # Clean up any role-specific session data if needed
        if hasattr(request, 'session') and request.user.is_authenticated:
            self._cleanup_session_data(request)
            
        return response
    
    def _cleanup_session_data(self, request):
        """Clean up session data when switching roles."""
        current_role = request.session.get('user_role')
        if not current_role:
            return
            
        # Remove any session data that doesn't belong to the current role
        role_keys = ['admin', 'lecturer', 'student']
        for role in role_keys:
            if role != current_role and f'session_{role}' in request.session:
                del request.session[f'session_{role}']
        
        # Save the session if modified
        if request.session.modified:
            request.session.save()
