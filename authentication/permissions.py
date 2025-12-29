from rest_framework import permissions


class IsTenantUser(permissions.BasePermission):
    """
    First layer of defense: Ensures user is authenticated and has a tenant.
    
    This permission checks that:
    1. User is authenticated
    2. request.tenant is set by CurrentTenantMiddleware
    
    Use this as a basic permission class for all tenant-scoped endpoints.
    For object-level validation, combine with IsTenantMember.
    """

    def has_permission(self, request, view):
        """Check if user is authenticated and has a tenant assigned."""
        return request.user.is_authenticated and request.tenant is not None


class IsTenantMember(permissions.BasePermission):
    """
    Second layer of defense: Validates tenant_id in JWT token matches resources.
    
    This permission provides object-level validation by:
    1. Checking JWT token's tenant_id claim
    2. Comparing it against URL parameters or request data
    3. Validating object ownership at the object level
    
    Use this in combination with IsTenantUser for defense-in-depth security.
    """

    def has_permission(self, request, view):
        """Validate JWT token contains tenant_id and matches request context."""
        # Token claims available via request.auth (AccessToken)
        token = request.auth
        if not token:
            return False
        
        token_tenant_id = token.get("tenant_id")
        
        # If views accept tenant_id in URL or query, validate it matches token
        url_tenant_id = view.kwargs.get("tenant_id") or request.data.get("tenant_id")
        if url_tenant_id:
            return str(token_tenant_id) == str(url_tenant_id)
        
        # Fallback: allow if token contains tenant (object-level check will enforce)
        return token_tenant_id is not None

    def has_object_permission(self, request, view, obj):
        """Validate the object's tenant matches the token's tenant_id."""
        token = request.auth
        if not token:
            return False
        
        token_tenant_id = token.get("tenant_id")
        obj_tenant_id = getattr(obj, "tenant_id", None)
        
        # Handle both direct tenant_id and tenant FK
        if obj_tenant_id is None and hasattr(obj, "tenant"):
            obj_tenant_id = getattr(obj.tenant, "tenant_id", None)
        
        return str(token_tenant_id) == str(obj_tenant_id)
