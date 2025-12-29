"""
Mixins for tenant-aware viewsets.
"""

class TenantViewSetMixin:
    """
    Mixin to automatically filter querysets by the current tenant.
    
    This mixin should be used with Django REST Framework ViewSets to ensure
    that all queries are automatically scoped to the current tenant.
    """
    
    def get_queryset(self):
        """
        Filter the queryset to only include objects belonging to the current tenant.
        """
        queryset = super().get_queryset()
        
        # Check if the request has a tenant attribute (set by middleware)
        if hasattr(self.request, 'tenant') and self.request.tenant:
            # Filter by tenant if the model has a tenant field
            if hasattr(queryset.model, 'tenant'):
                return queryset.filter(tenant=self.request.tenant)
        
        return queryset
