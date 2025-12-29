Multi-Layer Tenant Security Implementation
Overview
Implemented a defense-in-depth security strategy for tenant isolation with three layers of protection.

Security Architecture
No
Yes
Fail
Pass
Token Invalid
Pass
Client Request
CurrentTenantMiddleware
User Authenticated?
request.tenant = None
request.tenant = user.tenant
IsTenantUser Permission
403 Forbidden
IsTenantMember Permission
TenantViewSetMixin
Queryset Filtered by Tenant
TenantManager.for_tenant
Return Tenant-Scoped Data
Three Layers of Defense
Layer 1: Middleware (CurrentTenantMiddleware)
File: 
middleware.py

Sets request.tenant from authenticated user:

request.tenant = user.tenant  # Attached to every request
Layer 2: Permission Classes
IsTenantUser (Basic Check)
File: 
permissions.py

Purpose: First line of defense - validates user has a tenant

def has_permission(self, request, view):
    return request.user.is_authenticated and request.tenant is not None
When it blocks:

User not authenticated
User has no tenant (e.g., superuser without tenant)
IsTenantMember (Token Validation)
File: 
permissions.py

Purpose: Second line of defense - validates JWT token tenant_id

Permission-level check:

def has_permission(self, request, view):
    token_tenant_id = request.auth.get("tenant_id")
    url_tenant_id = view.kwargs.get("tenant_id")
    return str(token_tenant_id) == str(url_tenant_id)
Object-level check:

def has_object_permission(self, request, view, obj):
    token_tenant_id = request.auth.get("tenant_id")
    obj_tenant_id = obj.tenant.tenant_id
    return str(token_tenant_id) == str(obj_tenant_id)
When it blocks:

JWT token missing or invalid
Token's tenant_id doesn't match URL parameter
Object's tenant doesn't match token's tenant_id
Layer 3: Queryset Filtering
TenantViewSetMixin
File: 
mixins.py

Purpose: Automatically filters all queries to tenant-scoped data

Features:

Auto-applies permissions: [IsAuthenticated, IsTenantUser, IsTenantMember]
Smart queryset filtering: Uses TenantManager.for_tenant() if available
Fallback filtering: Direct filter(tenant=tenant) if no manager
def get_queryset(self):
    queryset = super().get_queryset()
    tenant = self.request.tenant
    
    if hasattr(queryset, 'for_tenant'):
        return queryset.for_tenant(tenant)
    
    return queryset.filter(tenant=tenant)
TenantManager
File: 
managers.py

Applied to all tenant-owned models:

Category.objects.for_tenant(tenant)
Product.objects.for_tenant(tenant)
StockMovement.objects.for_tenant(tenant)
Staff.objects.for_tenant(tenant)
Usage Example
Creating a ViewSet
from rest_framework.viewsets import ModelViewSet
from authentication.mixins import TenantViewSetMixin
from inventory.models import Product
from inventory.serializers import ProductSerializer
class ProductViewSet(TenantViewSetMixin, ModelViewSet):
    """
    Product API with automatic tenant isolation.
    
    Security is automatically applied:
    - IsAuthenticated: User must be logged in
    - IsTenantUser: User must have a tenant
    - IsTenantMember: JWT token must match tenant
    - Queryset: Filtered to user's tenant only
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    # Permissions inherited from TenantViewSetMixin
    # Can override if needed:
    # permission_classes = [IsAuthenticated, IsTenantUser]
What Happens on Request
Middleware: Sets request.tenant from user
IsTenantUser: Checks request.tenant is not None
IsTenantMember: Validates JWT tenant_id claim
get_queryset(): Filters to Product.objects.for_tenant(request.tenant)
Result: User only sees their tenant's products
Security Benefits
Attack Vector	Protection
Token tampering	JWT signature validation + tenant_id claim check
Cross-tenant access	Queryset filtered at DB level
Missing tenant	IsTenantUser blocks request early
URL manipulation	IsTenantMember validates URL tenant_id matches token
Object access	has_object_permission validates object ownership
Files Modified
New Permission Class
permissions.py
 - Added 
IsTenantUser
Enhanced Files
permissions.py
 - Enhanced 
IsTenantMember
 with better object-level checks
mixins.py
 - Added default permissions and smart queryset filtering
Existing Components (Unchanged)
middleware.py
 - 
CurrentTenantMiddleware
managers.py
 - 
TenantManager
Best Practices
IMPORTANT

Always use 
TenantViewSetMixin
 for tenant-scoped ViewSets to ensure all three security layers are active.

TIP

Override permission_classes in child ViewSets only when you need additional permissions, not fewer. Never remove tenant security permissions.

WARNING

Do not bypass queryset filtering by using Model.objects.all() directly in views. Always use self.get_queryset().