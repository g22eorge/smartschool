# Import all views from our modules
from .auth import login_view, logout_view
from .qr import generate_qr, view_qr, deactivate_qr, qr_history
from .reports import attendance_report, download_attendance
from .api import api_login, api_logout, api_get_modules, api_generate_qr, api_record_attendance
from .health import HealthCheckView

# Make these available when importing from attendance.views
__all__ = [
    'login_view', 'logout_view',
    'generate_qr', 'view_qr', 'deactivate_qr', 'qr_history',
    'attendance_report', 'download_attendance',
    'api_login', 'api_logout', 'api_get_modules', 'api_generate_qr', 'api_record_attendance',
    'HealthCheckView'
]
