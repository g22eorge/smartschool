#!/usr/bin/env python3
"""
Security check script for Django project.
Run this script to verify security settings.
"""
import os
import sys
import django
from django.conf import settings
from django.core.checks import Tags, run_checks

def check_security():
    """Check security settings and configurations."""
    print("\n=== Security Check ===\n")
    
    # Check debug mode
    debug_status = "ENABLED (Security Risk!)" if settings.DEBUG else "DISABLED (Good)"
    print(f"Debug Mode: {debug_status}")
    
    # Check allowed hosts
    if not settings.ALLOWED_HOSTS:
        print("WARNING: ALLOWED_HOSTS is empty (Security Risk!)")
    else:
        print(f"Allowed Hosts: {', '.join(settings.ALLOWED_HOSTS) or 'Not Set'}")
    
    # Check security settings
    security_settings = [
        ('SECURE_SSL_REDIRECT', 'HTTPS Redirection'),
        ('SESSION_COOKIE_SECURE', 'Secure Session Cookies'),
        ('CSRF_COOKIE_SECURE', 'Secure CSRF Cookies'),
        ('SECURE_BROWSER_XSS_FILTER', 'XSS Filter'),
        ('SECURE_CONTENT_TYPE_NOSNIFF', 'Content Type NoSniff'),
        ('X_FRAME_OPTIONS', 'Clickjacking Protection'),
    ]
    
    for setting, description in security_settings:
        value = getattr(settings, setting, None)
        status = "ENABLED" if value else "DISABLED"
        print(f"{description} ({setting}): {status}")
    
    # Check HSTS settings
    if getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0:
        hsts_status = f"ENABLED ({settings.SECURE_HSTS_SECONDS} seconds)"
        if getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False):
            hsts_status += " (includes subdomains)"
        if getattr(settings, 'SECURE_HSTS_PRELOAD', False):
            hsts_status += " (preload enabled)"
    else:
        hsts_status = "DISABLED"
    print(f"HSTS (HTTP Strict Transport Security): {hsts_status}")
    
    # Run Django's built-in security checks
    print("\nRunning Django security checks...")
    from django.core.checks.registry import registry
    
    # Get all registered checks
    all_checks = registry.get_checks()
    
    # Filter for security-related checks
    security_checks = [
        check for check in all_checks 
        if hasattr(check, 'tags') and 'security' in check.tags
    ]
    
    # Run only security checks
    from django.core.checks import run_checks
    from django.core.checks.messages import DEBUG, INFO, WARNING, ERROR
    
    # Run all checks and filter for security-related ones
    all_issues = run_checks()
    security_issues = [
        issue for issue in all_issues 
        if hasattr(issue, 'hint') and 'security' in getattr(issue, 'hint', '').lower()
    ]
    
    if not security_issues:
        print("No security issues found!")
    else:
        for issue in security_issues:
            print(f"\n{issue.level.upper()}: {issue.msg}")
            if hasattr(issue, 'hint') and issue.hint:
                print(f"Hint: {issue.hint}")

if __name__ == "__main__":
    # Set up Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_auth.settings')
    django.setup()
    
    check_security()
