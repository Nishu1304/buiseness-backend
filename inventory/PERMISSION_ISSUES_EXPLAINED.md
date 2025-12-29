# Permission Issues - Root Cause & Solution

## 🔴 Problem

Both tenant users and admins are getting **"You do not have permission to perform this action"** errors when trying to access inventory endpoints.

## 🔍 Root Cause Analysis

### Issue 1: Nullable Tenant Field
In `authentication/models.py` (lines 119-126), the `tenant` field is **nullable**:

```python
tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    related_name='users',
    null=True,        # ❌ Tenant can be None
    blank=True,       # ❌ Tenant is optional
    help_text="The tenant this user belongs to"
)
```

This means:
- ✅ **Superusers** - Don't have a tenant (system-wide access)
- ⚠️ **Regular users** - Might not have a tenant assigned
- ⚠️ **Tenant admins** - Might not have a tenant assigned

### Issue 2: Strict Permission Check
In `core/permissions.py` (line 24), the `IsTenantUser` permission requires a tenant:

```python
if not hasattr(request, 'tenant') or not request.tenant:
    return False  # ❌ Rejects users without tenant
```

### Issue 3: Middleware Crash Risk
The original middleware in `core/middleware.py` (line 13) directly accessed `user.tenant`:

```python
request.tenant = user.tenant  # ❌ Could crash if attribute doesn't exist
```

## ✅ Fixes Applied

### Fix 1: Safe Middleware Access ✓
Updated `core/middleware.py` to safely access the tenant:

```python
# Before (UNSAFE):
request.tenant = user.tenant

# After (SAFE):
request.tenant = getattr(user, 'tenant', None)
```

This prevents crashes but doesn't solve the permission issue.

## 🎯 Solutions

You have **3 options** to fix the permission issue:

### Option 1: Ensure All Users Have Tenants (Recommended)

**When creating users**, always assign a tenant:

```python
# In Django admin or user creation
user = User.objects.create_user(
    email="user@example.com",
    password="password",
    tenant=tenant_instance,  # ✅ Always assign tenant
    role="Admin"
)
```

**Check existing users:**
```python
# In Django shell
python manage.py shell

from authentication.models import User
users_without_tenant = User.objects.filter(tenant__isnull=True, is_superuser=False)
print(f"Users without tenant: {users_without_tenant.count()}")
for user in users_without_tenant:
    print(f"  - {user.email} (role: {user.role})")
```

### Option 2: Make Tenant Required (Database Change)

Update the User model to make tenant required for non-superusers:

```python
# In authentication/models.py
tenant = models.ForeignKey(
    Tenant,
    on_delete=models.CASCADE,
    related_name='users',
    null=False,      # ✅ Tenant is required
    blank=False,     # ✅ Must be provided
    help_text="The tenant this user belongs to"
)
```

Then run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

⚠️ **Warning**: This will fail if you have existing users without tenants!

### Option 3: Relax Permission Check (Not Recommended)

Modify `core/permissions.py` to allow admins without tenants:

```python
def has_permission(self, request, view):
    # User must be authenticated
    if not request.user or not request.user.is_authenticated:
        return False
    
    # Allow superusers
    if request.user.is_superuser:
        return True
    
    # Check if request has a tenant (set by middleware)
    if not hasattr(request, 'tenant') or not request.tenant:
        return False
    
    return True
```

⚠️ **Warning**: This breaks tenant isolation for superusers!

## 🔧 Recommended Action Plan

1. **Check your users** - See which users don't have tenants
2. **Assign tenants** - Update users to have proper tenant assignments
3. **Test login** - Try logging in with a user that has a tenant assigned

### Quick Check Command

```bash
python manage.py shell
```

```python
from authentication.models import User, Tenant

# List all users and their tenants
for user in User.objects.all():
    tenant_name = user.tenant.business_name if user.tenant else "NO TENANT"
    print(f"{user.email} - Role: {user.role} - Tenant: {tenant_name}")

# If you need to assign a tenant to a user:
tenant = Tenant.objects.first()  # or get specific tenant
user = User.objects.get(email="your-user@example.com")
user.tenant = tenant
user.save()
print(f"✓ Assigned {tenant.business_name} to {user.email}")
```

## 📝 Summary

The permission error happens because:
1. Users don't have a `tenant` assigned
2. The `IsTenantUser` permission requires a tenant
3. Without a tenant, `request.tenant` is `None`, failing the check

**Solution**: Assign tenants to all your users, or modify the permission logic to handle users without tenants appropriately.
