from django.shortcuts import render
from django.views import View
from django.conf import settings
from django.http import HttpResponse, HttpResponseServerError
import os

class TestView(View):
    def get(self, request):
        # Minimal context for the test page
        context = {
            'debug': settings.DEBUG,
            'static_url': settings.STATIC_URL or '/static/',
            'static_root': str(settings.STATIC_ROOT) if settings.STATIC_ROOT else 'Not set',
            'static_dirs': [str(d) for d in settings.STATICFILES_DIRS],
        }
        return render(request, 'minimal_test.html', context)

class StaticFilesDebugView(View):
    def get(self, request):
        """
        A view to help debug static files issues.
        Returns a simple HTML page with direct links to static files.
        """
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Static Files Debug</title>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
                .container { max-width: 800px; margin: 0 auto; }
                .test-box { 
                    width: 200px; 
                    height: 100px; 
                    background-color: #4CAF50; 
                    color: white; 
                    display: flex; 
                    align-items: center; 
                    justify-content: center; 
                    margin: 20px 0; 
                    padding: 10px;
                }
                .success { color: #4CAF50; }
                .error { color: #f44336; }
                pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
                .section { margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Static Files Debug</h1>
                
                <div class="section">
                    <h2>Test Box</h2>
                    <div class="test-box">
                        This is a test box with inline styles
                    </div>
                    <p>If you see a green box above, inline styles are working.</p>
                </div>
                
                <div class="section">
                    <h2>Static Files</h2>
                    <p>Click the links below to test if static files are accessible:</p>
                    <ul>
                        <li><a href="/static/css/styles.css" target="_blank">/static/css/styles.css</a></li>
                        <li><a href="/static/css/theme.css" target="_blank">/static/css/theme.css</a></li>
                        <li><a href="/static/css/custom.css" target="_blank">/static/css/custom.css</a></li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>Settings</h2>
                    <pre>DEBUG = {settings.DEBUG}
STATIC_URL = '{settings.STATIC_URL}'
STATIC_ROOT = '{settings.STATIC_ROOT}'
STATICFILES_DIRS = {[str(d) for d in settings.STATICFILES_DIRS]}
STATICFILES_FINDERS = {settings.STATICFILES_FINDERS}
INSTALLED_APPS = {[app for app in settings.INSTALLED_APPS if 'static' in app.lower()]}</pre>
                </div>
                
                <div class="section">
                    <h2>File System Check</h2>
                    <p>Checking if static files exist on disk:</p>
                    <pre>"""
        
        # Check if static files exist
        static_checks = []
        static_files = [
            os.path.join(settings.BASE_DIR, 'static', 'css', 'styles.css'),
            os.path.join(settings.BASE_DIR, 'static', 'css', 'theme.css'),
            os.path.join(settings.BASE_DIR, 'static', 'css', 'custom.css'),
        ]
        
        for file_path in static_files:
            exists = os.path.exists(file_path)
            static_checks.append(f"{file_path}: {'✓' if exists else '✗'}")
        
        html_content += '\n'.join(static_checks)
        html_content += """
                    </pre>
                </div>
                
                <div class="section">
                    <h2>Next Steps</h2>
                    <p>If the static files are not loading:</p>
                    <ol>
                        <li>Check if the files exist in the correct location</li>
                        <li>Verify that <code>DEBUG = True</code> in settings.py</li>
                        <li>Make sure <code>django.contrib.staticfiles</code> is in <code>INSTALLED_APPS</code></li>
                        <li>Run <code>python manage.py collectstatic</code> if needed</li>
                        <li>Check the browser's developer console for 404 errors</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HttpResponse(html_content)
