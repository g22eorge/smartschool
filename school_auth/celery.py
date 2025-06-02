import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_auth.settings')

app = Celery('school_auth')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Configure periodic tasks
app.conf.beat_schedule = {
    'deactivate-expired-qrcodes': {
        'task': 'attendance.tasks.deactivate_expired_qrcodes',
        'schedule': 300.0,  # Every 5 minutes
    },
    'generate-attendance-reports': {
        'task': 'attendance.tasks.generate_daily_attendance_reports',
        'schedule': crontab(hour=0, minute=30),  # Daily at 00:30
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
