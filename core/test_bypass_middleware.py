from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

class BypassMiddlewareView(View):
    """
    A view that bypasses all middleware to test if they're causing issues.
    """
    @method_decorator(csrf_exempt)
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Bypass Middleware Test</title>
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
                    background-color: #4CAF50;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px auto;
                    font-size: 24px;
                    font-weight: bold;
                    border-radius: 8px;
                }
                .success {
                    color: #4CAF50;
                    text-align: center;
                    margin: 20px 0;
                    font-size: 18px;
                }
                pre {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 4px;
                    overflow-x: auto;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Middleware Bypass Test</h1>
                
                <div class="test-box">
                    GREEN BOX
                </div>
                
                <div class="success">
                    ✓ This view bypasses all middleware
                </div>
                
                <h2>Debug Information:</h2>
                <pre>{
  "middleware_bypassed": true,
  "content_type": "text/html; charset=utf-8",
  "view_name": "BypassMiddlewareView"
}</pre>
                
                <p>If you see the green box, the issue is caused by one of the middleware components.</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html, content_type="text/html; charset=utf-8")
