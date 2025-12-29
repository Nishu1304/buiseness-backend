"""
Custom authentication classes for the BOS system.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthenticationWithTenant(JWTAuthentication):
    """
    Custom JWT authentication that also sets request.tenant.
    
    This solves the issue where middleware runs before JWT authentication,
    so request.tenant would be None even though the user has a tenant.
    
    By setting the tenant here (after successful JWT auth), we ensure
    that request.tenant is available for permission checks and view logic.
    """
    
    def authenticate(self, request):
        """
        Authenticate the request and set the tenant.
        
        Returns:
            tuple: (user, token) if authentication successful
            None: if authentication failed
        """
        # Call parent JWT authentication
        result = super().authenticate(request)
        
        if result is not None:
            user, token = result
            
            # Set tenant on request from authenticated user
            request.tenant = getattr(user, 'tenant', None)
        
        return result
