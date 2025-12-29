"""
Custom permissions for tenant-based access control.
"""
from rest_framework import permissions


class IsTenantUser(permissions.BasePermission):
    """
    Permission class to check if the user belongs to a tenant.
    
    This permission ensures that only authenticated users who are associated
    with a tenant can access the view.
    """
    
    def has_permission(self, request, view):
        """
        Check if the user is authenticated and has a tenant.
        """
        # User must be authenticated
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check if request has a tenant (set by middleware)
        if not hasattr(request, 'tenant') or not request.tenant:
            return False
        
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Check if the object belongs to the user's tenant.
        """
        # Check if the object has a tenant field
        if hasattr(obj, 'tenant'):
            return obj.tenant == request.tenant
        
        return True
