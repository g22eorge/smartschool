from django.shortcuts import render
from django.views import View
from django.conf import settings
import os
import json

class StaticFilesTestView(View):
    def get(self, request):
        # Test if static files are accessible
        static_url = settings.STATIC_URL
        static_root = settings.STATIC_ROOT
        static_dirs = settings.STATICFILES_DIRS
        
        # Check if static files exist
        test_file = os.path.join(static_root, 'img/favicon.ico') if static_root else None
        file_exists = os.path.exists(test_file) if test_file else False
        
        context = {
            'debug': settings.DEBUG,
            'static_url': static_url,
            'static_root': static_root,
            'static_dirs': static_dirs,
            'file_exists': file_exists,
            'debug_info': json.dumps({
                'DEBUG': settings.DEBUG,
                'STATIC_URL': static_url,
                'STATIC_ROOT': static_root,
                'STATICFILES_DIRS': [str(d) for d in static_dirs],
                'INSTALLED_APPS': settings.INSTALLED_APPS,
            }, indent=2)
        }
        
        return render(request, 'test_page.html', context)
