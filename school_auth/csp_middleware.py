"""
CSP Nonce Middleware for Django.
"""
import os
import base64
from django.utils.deprecation import MiddlewareMixin

class CSPNonceMiddleware(MiddlewareMixin):
    """
    Middleware that adds a unique nonce to each request for use in CSP headers.
    The nonce can be accessed in templates via request.csp_nonce.
    """
    def process_request(self, request):
        # Generate a random nonce for each request
        nonce = base64.b64encode(os.urandom(32)).decode('utf-8')
        request.csp_nonce = nonce
        return None
