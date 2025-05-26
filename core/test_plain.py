from django.http import HttpResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.shortcuts import render
from django.views.generic import TemplateView

class CSSTestView(TemplateView):
    template_name = 'css_test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['test_message'] = 'This is a test message from the view'
        return context

class PlainTextView(View):
    """View for testing plain HTML rendering"""
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>HTML Rendering Test</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .test-box {
                    width: 200px;
                    height: 200px;
                    background-color: #4CAF50;  /* Green */
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px auto;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 8px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>HTML Rendering Test</h1>
                <p>If you see a green box below, HTML and CSS are working correctly.</p>
                
                <div class="test-box">
                    GREEN BOX
                </div>
                
                <h2>Debug Information:</h2>
                <p>This page is served with <code>Content-Type: text/html</code></p>
                <p>If you see this styled page, the issue is with your template rendering.</p>
                <p>If you still see raw HTML, there might be middleware modifying the response.</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content, content_type="text/html; charset=utf-8")
