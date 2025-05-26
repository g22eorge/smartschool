"""
Security middleware for Django application.
"""
from django.conf import settings
from django.http import HttpResponsePermanentRedirect
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers to responses.
    """
    def process_response(self, request, response):
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Only add these headers if not already set
        if 'Content-Security-Policy' not in response:
            # Generate a nonce for inline scripts and styles
            nonce = getattr(request, 'csp_nonce', '')
            nonce_value = f"'nonce-{nonce}'" if nonce else ''
            
            # Define the CSP policy with nonce support
            csp_policy = [
                "default-src 'self';",
                f"script-src 'self' 'unsafe-eval' 'strict-dynamic' {nonce_value} https://code.jquery.com https://cdnjs.cloudflare.com https://kit.fontawesome.com;",
                f"script-src-elem 'self' 'unsafe-inline' {nonce_value} https://code.jquery.com https://cdnjs.cloudflare.com https://kit.fontawesome.com;",
                f"style-src 'self' 'unsafe-inline' {nonce_value} https://fonts.googleapis.com https://cdnjs.cloudflare.com;",
                f"style-src-elem 'self' 'unsafe-inline' {nonce_value} https://fonts.googleapis.com https://cdnjs.cloudflare.com;",
                "img-src 'self' data: https:;",
                "font-src 'self' data: https: https://fonts.gstatic.com https://cdnjs.cloudflare.com https://fonts.googleapis.com;",
                "connect-src 'self' https:;",
                "frame-src 'self' https:;",
                "object-src 'none';",
                "base-uri 'self';",
                "form-action 'self';",
                "frame-ancestors 'none';",
                "upgrade-insecure-requests;",
                "block-all-mixed-content;"
            ]
            
            # Set the CSP header
            response['Content-Security-Policy'] = ' '.join(csp_policy)
                
        # Add Cross-Origin Resource Policy
        if 'Cross-Origin-Resource-Policy' not in response:
            response['Cross-Origin-Resource-Policy'] = 'same-site'
            
        # Add Cross-Origin-Embedder-Policy
        if 'Cross-Origin-Embedder-Policy' not in response:
            response['Cross-Origin-Embedder-Policy'] = 'credentialless'
            
        if 'Referrer-Policy' not in response:
            response['Referrer-Policy'] = 'same-origin'
            
        if 'Permissions-Policy' not in response:
            response['Permissions-Policy'] = (
                'camera=(), microphone=(), geolocation=(), '
                'payment=(), usb=()'
            )
            
        if 'Cross-Origin-Opener-Policy' not in response:
            response['Cross-Origin-Opener-Policy'] = 'same-origin'
            
        if 'Cross-Origin-Embedder-Policy' not in response:
            response['Cross-Origin-Embedder-Policy'] = 'require-corp'
            
        return response


class HSTSMiddleware(MiddlewareMixin):
    """
    Middleware to handle HTTP Strict Transport Security (HSTS) headers.
    """
    def process_response(self, request, response):
        if request.is_secure():
            if 'Strict-Transport-Security' not in response:
                response['Strict-Transport-Security'] = (
                    f'max-age={settings.SECURE_HSTS_SECONDS}; '
                    f'includeSubDomains; preload'
                )
        return response


class SSLRedirectMiddleware(MiddlewareMixin):
    """
    Middleware to redirect HTTP to HTTPS.
    """
    def process_request(self, request):
        # Skip redirection in debug mode
        if settings.DEBUG:
            return None
            
        if not any([
            request.path.startswith(path) for path in getattr(settings, 'SECURE_SSL_REDIRECT_EXEMPT', [])
        ]):
            return self._redirect(request)

    def _redirect(self, request):
        if settings.SECURE_SSL_REDIRECT and not request.is_secure():
            return HttpResponsePermanentRedirect(
                'https://%s%s' % (request.get_host(), request.get_full_path())
            )
        return None
