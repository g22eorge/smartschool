import time
import logging
from django.core.management.base import BaseCommand
from django.db import connection, OperationalError
from django.core.cache import cache
from django.conf import settings
import redis
import psutil
import requests

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check system health and report any issues'
    
    def handle(self, *args, **options):
        """Handle the management command."""
        checks = {
            'database': self.check_database,
            'cache': self.check_cache,
            'disk_space': self.check_disk_space,
            'memory': self.check_memory,
            'external_services': self.check_external_services,
        }
        
        results = {}
        overall_healthy = True
        
        for name, check_func in checks.items():
            try:
                result = check_func()
                results[name] = {
                    'status': 'healthy',
                    'details': result
                }
                self.stdout.write(self.style.SUCCESS(f"✓ {name}: Healthy"))
            except Exception as e:
                overall_healthy = False
                results[name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                self.stderr.write(self.style.ERROR(f"✗ {name}: {e}"))
        
        # Log overall status
        if overall_healthy:
            self.stdout.write(self.style.SUCCESS("\n✅ All systems operational"))
        else:
            self.stderr.write(self.style.ERROR("\n❌ Some systems are not healthy"))
        
        return results
    
    def check_database(self):
        """Check database connection and response time."""
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        response_time = (time.time() - start_time) * 1000  # in ms
        
        if response_time > 100:  # 100ms threshold
            logger.warning(f"Database response time is high: {response_time:.2f}ms")
        
        return {
            'response_time_ms': round(response_time, 2),
            'database': settings.DATABASES['default']['ENGINE'],
            'connection_ok': True
        }
    
    def check_cache(self):
        """Check cache connectivity and response time."""
        test_key = 'health_check'
        test_value = 'test_value'
        
        # Test set
        start_time = time.time()
        cache.set(test_key, test_value, 10)
        set_time = (time.time() - start_time) * 1000  # in ms
        
        # Test get
        start_time = time.time()
        value = cache.get(test_key)
        get_time = (time.time() - start_time) * 1000  # in ms
        
        if value != test_value:
            raise Exception(f"Cache value mismatch: expected {test_value}, got {value}")
        
        return {
            'set_time_ms': round(set_time, 2),
            'get_time_ms': round(get_time, 2),
            'backend': settings.CACHES['default']['BACKEND'],
            'connection_ok': True
        }
    
    def check_disk_space(self):
        """Check available disk space."""
        disk = psutil.disk_usage('/')
        free_gb = disk.free / (1024 * 1024 * 1024)
        total_gb = disk.total / (1024 * 1024 * 1024)
        used_percent = disk.percent
        
        if used_percent > 90:
            logger.error(f"Disk space critically low: {used_percent:.1f}% used")
        elif used_percent > 80:
            logger.warning(f"Disk space getting low: {used_percent:.1f}% used")
        
        return {
            'free_gb': round(free_gb, 2),
            'total_gb': round(total_gb, 2),
            'used_percent': used_percent,
            'status': 'ok' if used_percent < 90 else 'warning' if used_percent < 95 else 'critical'
        }
    
    def check_memory(self):
        """Check system memory usage."""
        memory = psutil.virtual_memory()
        used_percent = memory.percent
        available_gb = memory.available / (1024 * 1024 * 1024)
        
        if used_percent > 90:
            logger.error(f"Memory usage critically high: {used_percent:.1f}% used")
        elif used_percent > 80:
            logger.warning(f"Memory usage high: {used_percent:.1f}% used")
        
        return {
            'available_gb': round(available_gb, 2),
            'used_percent': used_percent,
            'status': 'ok' if used_percent < 85 else 'warning' if used_percent < 95 else 'critical'
        }
    
    def check_external_services(self):
        """Check connectivity to external services."""
        services = {}
        
        # Check Redis
        redis_url = settings.CELERY_BROKER_URL or 'redis://localhost:6379/0'
        try:
            r = redis.from_url(redis_url)
            start_time = time.time()
            r.ping()
            redis_ping = (time.time() - start_time) * 1000
            services['redis'] = {
                'status': 'ok',
                'response_time_ms': round(redis_ping, 2)
            }
        except Exception as e:
            services['redis'] = {
                'status': 'error',
                'error': str(e)
            }
        
        # Add more external service checks as needed
        
        return services
