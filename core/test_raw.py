from django.http import HttpResponse
from django.views import View
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator

class RawResponseView(View):
    """
    A view that returns a raw HTTP response without any middleware processing.
    """
    @method_decorator(require_http_methods(["GET"]))
    def get(self, request):
        # This is a raw HTTP response that should bypass most middleware
        raw_response = (
            b'HTTP/1.1 200 OK\r\n'
            b'Content-Type: text/html; charset=utf-8\r\n'
            b'\r\n'
            b'<!DOCTYPE html>\n'
            b'<html>\n'
            b'<head>\n'
            b'<title>Raw Response Test</title>\n'
            b'<meta charset="UTF-8">\n'
            b'<style>\n'
            b'  body { font-family: Arial, sans-serif; padding: 20px; }\n'
            b'  .test { width: 200px; height: 200px; background: #4CAF50; color: white; \
                   display: flex; align-items: center; justify-content: center; \
                   margin: 20px auto; font-size: 24px; border-radius: 8px; }\n'
            b'  .success { color: #4CAF50; text-align: center; }\n'
            b'</style>\n'
            b'</head>\n'
            b'<body>\n'
            b'  <h1>Raw HTTP Response Test</h1>\n'
            b'  <p>This response is sent directly at the WSGI level.</p>\n'
            b'  <div class="test">GREEN BOX</div>\n'
            b'  <p class="success">If you see a green box, the issue is with Django\'s middleware.</p>\n'
            b'</body>\n'
            b'</html>'
        )
        
        # Create a raw HTTP response
        response = HttpResponse(
            content=raw_response.split(b'\r\n\r\n', 1)[1],  # Remove the HTTP headers
            content_type='text/html; charset=utf-8',
            status=200
        )
        
        # Set headers manually
        for header_line in raw_response.split(b'\r\n'):
            if b': ' in header_line:
                header, value = header_line.split(b': ', 1)
                response[header.decode('ascii')] = value.decode('ascii')
        
        return response
