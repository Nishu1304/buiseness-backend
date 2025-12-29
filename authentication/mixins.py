from rest_framework import permissions
from .permissions import IsTenantUser, IsTenantMember


class TenantViewSetMixin:
    """
    Mixin for ViewSets that automatically filters queryset by tenant.
    
    This mixin provides:
    1. Automatic queryset filtering by request.tenant
    2. Default permission classes for tenant security (can be overridden)
    3. Defense-in-depth security with both middleware and token validation
    4. Automatic tenant assignment on create/update operations
    
    Usage:
        class ProductViewSet(TenantViewSetMixin, ModelViewSet):
            queryset = Product.objects.all()
            serializer_class = ProductSerializer
    """
    
    # Default permission classes - can be overridden in child classes
    permission_classes = [permissions.IsAuthenticated, IsTenantUser, IsTenantMember]

    def get_queryset(self):
        """
        Filter queryset to only include objects belonging to the user's tenant.
        
        This works in conjunction with:
        - CurrentTenantMiddleware (sets request.tenant)
        - TenantManager (provides for_tenant() method)
        - IsTenantUser permission (validates tenant exists)
        - IsTenantMember permission (validates token tenant_id)
        """
        queryset = super().get_queryset()
        tenant = self.request.tenant
        
        # Use TenantManager's for_tenant method if available
        if hasattr(queryset, 'for_tenant'):
            return queryset.for_tenant(tenant)
        
        # Fallback to direct filter
        return queryset.filter(tenant=tenant)
    
    def perform_create(self, serializer):
        """
        Force tenant assignment on creation.
        
        This is a critical security measure that prevents users from creating
        records with a different tenant_id by sending it in the request payload.
        The tenant is always set from request.tenant (validated by middleware).
        """
        serializer.save(tenant=self.request.tenant)
    
    def perform_update(self, serializer):
        """
        Force tenant assignment on update.
        
        This prevents users from changing the tenant of an existing record
        by sending a different tenant_id in the update payload.
        The tenant is always preserved from request.tenant.
        """
        serializer.save(tenant=self.request.tenant)