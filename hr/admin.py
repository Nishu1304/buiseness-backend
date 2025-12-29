from django.contrib import admin
from .models import Staff, Attendance


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """Admin interface for Staff model."""
    list_display = (
        'staff_id', 
        'name', 
        'position', 
        'phone', 
        'joining_date',   # Fixed: use model field name, not serializer alias
        'salary', 
        'tenant', 
        'is_active'
    )
    list_filter = ('position', 'is_active', 'tenant')
    search_fields = ('name', 'phone', 'email')
    ordering = ('name',)
    readonly_fields = ('staff_id', 'created_at', 'updated_at')
    date_hierarchy = 'joining_date'  # Fixed: use model field name
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'phone', 'email')
        }),
        ('Employment Details', {
            'fields': ('joining_date', 'salary', 'is_active')
        }),
        ('Documents', {
            'fields': ('aadhaar_file',)
        }),
        ('Metadata', {
            'fields': ('tenant', 'staff_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    """Admin interface for Attendance model."""
    list_display = (
        'attendance_id', 
        'staff', 
        'date', 
        'status', 
        'tenant'
    )
    list_filter = ('status', 'date', 'tenant')
    search_fields = ('staff__name',)
    ordering = ('-date',)
    readonly_fields = ('attendance_id', 'created_at')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Attendance Details', {
            'fields': ('staff', 'date', 'status')
        }),
        ('Metadata', {
            'fields': ('tenant', 'attendance_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )
