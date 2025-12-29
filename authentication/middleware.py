# Optional but we are using
from django.utils.deprecation import MiddlewareMixin

class TenantFromJWTMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = getattr(request, "auth", None)
        tenant_id = None
        if token:
            tenant_id = token.get("tenant_id")
        request.tenant_id = tenant_id
