import logging
import time
import json
from datetime import datetime
from django.http import JsonResponse
from django.views import View
from django.conf import settings
from django.db import connection
from django.core.cache import cache
import psutil
import redis

logger = logging.getLogger(__name__)

class HealthCheckView(View):
    """
    Health check endpoint for monitoring the application status.
    Returns 200 if the application is healthy, 500 otherwise.
    """
    def get(self, request, *args, **kwargs):
        # Initialize response data
        checks = {}
        status_code = 200
        
        # Check database connection
        db_status = self._check_database()
        checks['database'] = db_status
        if not db_status['healthy']:
            status_code = 500
        
        # Check cache
        cache_status = self._check_cache()
        checks['cache'] = cache_status
        if not cache_status['healthy']:
            status_code = 500
            
        # Check disk space
        disk_status = self._check_disk_space()
        checks['disk_space'] = disk_status
        if disk_status['status'] == 'critical':
            status_code = 500
            
        # Check memory usage
        memory_status = self._check_memory()
        checks['memory'] = memory_status
        if memory_status['status'] == 'critical':
            status_code = 500
            
        # Check external services
        services_status = self._check_external_services()
        checks['external_services'] = services_status
        if any(not s['healthy'] for s in services_status.values()):
            status_code = 500
        
        # Prepare response
        response_data = {
            'status': 'healthy' if status_code == 200 else 'unhealthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': checks,
            'version': getattr(settings, 'VERSION', 'dev'),
        }
        
        return JsonResponse(response_data, status=status_code)
    
    def _check_database(self):
        """Check database connectivity and response time."""
        try:
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            response_time = (time.time() - start_time) * 1000  # in ms
            
            return {
                'healthy': True,
                'response_time_ms': round(response_time, 2),
                'database': settings.DATABASES['default']['ENGINE'],
            }
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
            }
    
    def _check_cache(self):
        """Check cache connectivity and response time."""
        test_key = 'health_check'
        test_value = 'test_value'
        
        try:
            # Test set
            start_time = time.time()
            cache.set(test_key, test_value, 10)
            set_time = (time.time() - start_time) * 1000  # in ms
            
            # Test get
            start_time = time.time()
            value = cache.get(test_key)
            get_time = (time.time() - start_time) * 1000  # in ms
            
            if value != test_value:
                raise ValueError(f"Cache value mismatch: expected {test_value}, got {value}")
            
            return {
                'healthy': True,
                'set_time_ms': round(set_time, 2),
                'get_time_ms': round(get_time, 2),
                'backend': settings.CACHES['default']['BACKEND'],
            }
        except Exception as e:
            logger.error(f"Cache check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
            }
    
    def _check_disk_space(self):
        """Check available disk space."""
        try:
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 * 1024 * 1024)
            used_percent = disk.percent
            
            status = 'ok'
            if used_percent > 90:
                status = 'critical'
                logger.error(f"Disk space critically low: {used_percent:.1f}% used")
            elif used_percent > 80:
                status = 'warning'
                logger.warning(f"Disk space getting low: {used_percent:.1f}% used")
            
            return {
                'healthy': status != 'critical',
                'status': status,
                'free_gb': round(free_gb, 2),
                'used_percent': used_percent,
            }
        except Exception as e:
            logger.error(f"Disk space check failed: {str(e)}")
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e),
            }
    
    def _check_memory(self):
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            available_gb = memory.available / (1024 * 1024 * 1024)
            
            status = 'ok'
            if used_percent > 90:
                status = 'critical'
                logger.error(f"Memory usage critically high: {used_percent:.1f}% used")
            elif used_percent > 80:
                status = 'warning'
                logger.warning(f"Memory usage high: {used_percent:.1f}% used")
            
            return {
                'healthy': status != 'critical',
                'status': status,
                'available_gb': round(available_gb, 2),
                'used_percent': used_percent,
            }
        except Exception as e:
            logger.error(f"Memory check failed: {str(e)}")
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e),
            }
    
    def _check_external_services(self):
        """Check connectivity to external services."""
        services = {}
        
        # Check Redis
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)
            start_time = time.time()
            r.ping()
            redis_ping = (time.time() - start_time) * 1000
            services['redis'] = {
                'healthy': True,
                'response_time_ms': round(redis_ping, 2),
            }
        except Exception as e:
            logger.error(f"Redis check failed: {str(e)}")
            services['redis'] = {
                'healthy': False,
                'error': str(e),
            }
        
        # Add more external service checks as needed
        
        return services
