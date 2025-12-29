from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Tenant, User

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """Admin interface for Tenant model."""
    list_display = ('tenant_id', 'business_name', 'plan', 'status', 'created_at', 'sub_end_date')
    list_filter = ('plan', 'status', 'created_at')
    search_fields = ('business_name',)
    ordering = ('-created_at',)
    readonly_fields = ('tenant_id', 'created_at')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model."""
    list_display = ('email', 'role', 'tenant', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'tenant')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    # Fields to display when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Organization', {'fields': ('tenant', 'staff_profile')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields to display when creating a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'tenant'),
        }),
    )
