# Postman Authentication Issue - Debugging Guide

## 🔍 Issue
Getting "not authorized" or "permission denied" in Postman for inventory endpoints.

## ✅ What We Know
1. User exists: `admin@gmail.com`
2. User has tenant: "SuperUser (Standard)"
3. Middleware is registered correctly
4. Login endpoint works (can get token)

## 🎯 Root Cause
The JWT authentication in DRF happens **during view processing**, not during middleware. This means:
1. Middleware runs → `request.user` is AnonymousUser → `request.tenant` = None
2. View runs → JWT auth happens → `request.user` is set
3. But `request.tenant` was already set to None in step 1!

## 🔧 Solution

We need to move tenant extraction to happen **after** JWT authentication, not in middleware.

### Option 1: Use a Custom Authentication Class (Recommended)

Create a custom JWT authentication that also sets the tenant.

**File**: `core/authentication.py` (create new file)

```python
from rest_framework_simplejwt.authentication import JWTAuthentication

class JWTAuthenticationWithTenant(JWTAuthentication):
    """
    Custom JWT authentication that also sets request.tenant
    """
    def authenticate(self, request):
        # Call parent authentication
        result = super().authenticate(request)
        
        if result is not None:
            user, token = result
            # Set tenant on request
            request.tenant = getattr(user, 'tenant', None)
        
        return result
```

**Then update** `core/settings.py`:

```python
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "core.authentication.JWTAuthenticationWithTenant",  # Use custom class
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}
```

### Option 2: Remove Middleware, Use Mixin

Remove `CurrentTenantMiddleware` from settings and ensure all viewsets use `TenantViewSetMixin` which sets the tenant.

**Update** `core/settings.py` - Remove this line:
```python
# 'core.middleware.CurrentTenantMiddleware',  # REMOVE THIS
```

**Ensure** `core/mixins.py` has:
```python
class TenantViewSetMixin:
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Set tenant on request if not already set
        if not hasattr(self.request, 'tenant'):
            self.request.tenant = getattr(self.request.user, 'tenant', None)
        
        # Filter by tenant if applicable
        if hasattr(self.request, 'tenant') and self.request.tenant:
            if hasattr(queryset.model, 'tenant'):
                return queryset.filter(tenant=self.request.tenant)
        
        return queryset
```

## 🚀 Quick Fix (Easiest)

I'll implement Option 1 for you - it's the cleanest solution.

## 📝 After Applying Fix

1. Restart Django server
2. In Postman:
   - Run "Login (Get Token)" with `admin@gmail.com` / `1234`
   - Token will be saved automatically
   - Try "List Categories" - should work now!

## 🧪 Test Commands

```powershell
# Test authentication
.\test_api_auth.ps1

# If it works, you'll see:
# ✓ Login successful!
# ✓ Categories endpoint working!
# ✓ Create category working!
```
