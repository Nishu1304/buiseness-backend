"""
Authentication models for the BOS system.

This module defines the core authentication models:
- Tenant: Represents a client organization (multi-tenancy)
- User: Custom user model using email as username
- UserManager: Manager for creating users and superusers
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class Tenant(models.Model):
    """
    Represents a client organization in the multi-tenant system.
    
    Each tenant is isolated from others and has their own subscription plan.
    All data in the system should be scoped to a tenant for data isolation.
    """
    tenant_id = models.BigAutoField(primary_key=True)
    business_name = models.CharField(max_length=255, help_text="Name of the client's business")
    plan = models.CharField(
        max_length=50,
        choices=[('Basic', 'Basic'), ('Standard', 'Standard')],
        help_text="Subscription plan type"
    )
    status = models.CharField(max_length=50, help_text="Tenant status (Active, Suspended, etc.)")
    created_at = models.DateTimeField(auto_now_add=True, help_text="When this tenant was created")
    sub_end_date = models.DateTimeField(help_text="Subscription expiration date")

    class Meta:
        db_table = 'auth_tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'

    def __str__(self):
        return f"{self.business_name} ({self.plan})"

class UserManager(BaseUserManager):
    """
    Custom manager for User model.
    
    This manager handles user creation with email as the primary identifier
    instead of username.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a regular user with the given email and password.
        
        Args:
            email: User's email address (required)
            password: User's password (required)
            **extra_fields: Additional fields like tenant, role, etc.
            
        Returns:
            User instance
            
        Raises:
            ValueError: If email is not provided
        """
        if not email:
            raise ValueError('The Email field must be set')
        
        # Normalize the email address
        email = self.normalize_email(email)
        
        # Create user instance
        user = self.model(email=email, **extra_fields)
        
        # Set password (hashed)
        user.set_password(password)
        
        # Save to database
        user.save(using=self._db)
        
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a superuser with the given email and password.
        
        Superusers have all permissions and can access Django admin.
        
        Args:
            email: Superuser's email address (required)
            password: Superuser's password (required)
            **extra_fields: Additional fields
            
        Returns:
            User instance with superuser privileges
        """
        # Set required superuser flags
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'Admin')

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Custom user model for authentication.
    
    Uses email instead of username for authentication.
    Each user belongs to a Tenant (except superusers) and has a role.
    Users may also have a linked Staff profile for HR tracking.
    """
    
    # Remove the username field (we use email instead)
    username = None
    
    # Primary key
    user_id = models.BigAutoField(primary_key=True)
    
    # Email is used for authentication (USERNAME_FIELD)
    email = models.EmailField(unique=True, help_text="User's email address (used for login)")
    
    # Link to tenant for multi-tenancy
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        help_text="The tenant this user belongs to"
    )
    
    # Link to staff profile (optional, for HR tracking)
    staff_profile = models.ForeignKey(
        'hr.Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_account',
        help_text="Linked staff profile if this user is an employee"
    )
    
    # User's role in the system
    role = models.CharField(
        max_length=50,
        choices=[('Admin', 'Admin'), ('Staff', 'Staff')],
        help_text="User's role (Admin has more permissions)"
    )
    
    # Use email as the login field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is already required by USERNAME_FIELD

    # Use our custom manager
    objects = UserManager()

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.email} ({self.role})"
