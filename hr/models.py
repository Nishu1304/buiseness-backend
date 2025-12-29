from django.db import models
from core.managers import TenantManager


class Staff(models.Model):
    """Staff member model for HR management."""
    staff_id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'authentication.Tenant', 
        on_delete=models.CASCADE, 
        related_name='staff_members'
    )
    name = models.CharField(max_length=255)
    position = models.CharField(max_length=100, default='Staff')  # Role in the shop
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)  # Optional
    joining_date = models.DateField(null=True, blank=True)  # Made optional for migration
    salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    aadhaar_file = models.FileField(upload_to='staff/aadhaar/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Staff Member'
        verbose_name_plural = 'Staff Members'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.position})"


class Attendance(models.Model):
    """Attendance record for staff members."""
    ATTENDANCE_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Leave', 'Leave'),
    ]
    
    attendance_id = models.BigAutoField(primary_key=True)
    tenant = models.ForeignKey(
        'authentication.Tenant', 
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    staff = models.ForeignKey(
        Staff, 
        on_delete=models.CASCADE, 
        related_name='attendance_records'
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=ATTENDANCE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Attendance Record'
        verbose_name_plural = 'Attendance Records'
        unique_together = ['staff', 'date']  # One attendance per staff per day
        ordering = ['-date']

    def __str__(self):
        return f"{self.staff.name} - {self.date} - {self.status}"
