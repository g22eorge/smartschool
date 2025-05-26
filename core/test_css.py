from django.http import HttpResponse
from django.views import View

class CSSTestView(View):
    def get(self, request):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CSS Test</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    padding: 20px; 
                    background-color: #f5f5f5;
                }
                .test-box {
                    width: 200px;
                    height: 200px;
                    background-color: #4CAF50;
                    color: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 24px;
                    font-weight: bold;
                    margin: 20px auto;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                }
                .success {
                    color: #4CAF50;
                    text-align: center;
                    font-size: 24px;
                    margin: 20px 0;
                }
            </style>
        </head>
        <body>
            <h1 style="text-align: center; color: #333;">CSS Test Page</h1>
            <div class="test-box">
                GREEN BOX
            </div>
            <p class="success">✓ If you see a green box, CSS is working!</p>
            
            <div style="text-align: center; margin-top: 50px;">
                <h3>Debug Info:</h3>
                <p>This page is served directly from the view without using any templates.</p>
                <p>If you see the green box, the issue is with your template rendering.</p>
                <p>If you don't see the green box, there might be a deeper issue with CSS processing.</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html)
