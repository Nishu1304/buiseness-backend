import logging
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from rest_framework import serializers
from .models import Tenant, User
from hr.models import Staff

# Initialize logger for this module
logger = logging.getLogger(__name__)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that adds tenant_id and role to token claims.
    
    This allows the frontend to know which tenant the user belongs to
    and what their role is without making additional API calls.
    """
    
    @classmethod
    def get_token(cls, user):
        """
        Override to add custom claims to the JWT token.
        
        Args:
            user: The authenticated User instance
            
        Returns:
            Token with additional claims: user_id, tenant_id, role
        """
        try:
            # Get the base token from parent class
            token = super().get_token(user)
            
            # Add user's primary key
            token["user_id"] = user.pk
            
            # Try to get tenant_id from user.tenant first
            tenant_id = getattr(user, "tenant_id", None)
            
            # If not found and user has a staff_profile, get it from there
            if not tenant_id and hasattr(user, "staff_profile"):
                try:
                    tenant_id = user.staff_profile.tenant_id
                    logger.debug(f"Tenant ID retrieved from staff_profile for user {user.email}")
                except Exception as e:
                    logger.warning(f"Could not retrieve tenant_id from staff_profile for user {user.email}: {e}")
                    tenant_id = None
            
            token["tenant_id"] = tenant_id
            token["role"] = getattr(user, "role", None)
            
            logger.info(f"Token generated successfully for user {user.email} (tenant: {tenant_id}, role: {token['role']})")
            return token
            
        except Exception as e:
            logger.error(f"Error generating token for user {user.email}: {e}", exc_info=True)
            raise

class TenantProvisioningSerializer(serializers.Serializer):
    """
    Serializer for creating a new tenant along with their initial admin user.
    
    This is an internal-only endpoint used by superadmins to onboard new clients.
    It creates three related objects in a single transaction:
    1. Tenant (the organization)
    2. Staff profile (for HR tracking)
    3. User account (for authentication)
    """
    
    business_name = serializers.CharField(max_length=255, help_text="Name of the tenant's business")
    plan = serializers.ChoiceField(
        choices=[('Basic', 'Basic'), ('Standard', 'Standard')],
        help_text="Subscription plan type"
    )
    email = serializers.EmailField(help_text="Email for the tenant's admin user (used for login)")
    password = serializers.CharField(write_only=True, help_text="Password for the admin user")
    first_name = serializers.CharField(max_length=255, required=False, help_text="Admin's first name")
    last_name = serializers.CharField(max_length=255, required=False, help_text="Admin's last name")
    phone = serializers.CharField(max_length=20, required=False, help_text="Admin's phone number")

    def validate_email(self, value):
        """
        Check that the email is not already in use.
        
        Args:
            value: The email address to validate
            
        Returns:
            The validated email
            
        Raises:
            ValidationError: If email already exists
        """
        if User.objects.filter(email=value).exists():
            logger.warning(f"Tenant provisioning failed: Email {value} already exists")
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """
        Create Tenant, Staff, and User in a single atomic transaction.
        
        Args:
            validated_data: Dictionary containing validated field data
            
        Returns:
            The created Tenant instance
            
        Raises:
            Exception: If any step in the creation process fails
        """
        from django.utils import timezone
        from datetime import timedelta

        business_name = validated_data.get('business_name')
        email = validated_data.get('email')
        
        try:
            with transaction.atomic():
                # 1. Create Tenant
                # Default subscription to 30 days from now
                sub_end_date = timezone.now() + timedelta(days=30)
                
                logger.info(f"Creating tenant: {business_name}")
                tenant = Tenant.objects.create(
                    business_name=business_name,
                    plan=validated_data['plan'],
                    status='Active',
                    sub_end_date=sub_end_date
                )
                logger.info(f"Tenant created successfully: {business_name} (ID: {tenant.tenant_id})")

                # 2. Create Staff Profile (for the Admin)
                staff_name = f"{validated_data.get('first_name', '')} {validated_data.get('last_name', '')}".strip() or email
                logger.info(f"Creating staff profile for: {staff_name}")
                
                staff = Staff.objects.create(
                    tenant=tenant,
                    name=staff_name,
                    email=email,
                    phone=validated_data.get('phone', ''),
                    role='Admin',
                    status='Active'
                )
                logger.info(f"Staff profile created successfully: {staff_name} (ID: {staff.staff_id})")

                # 3. Create User (Admin)
                logger.info(f"Creating admin user: {email}")
                user = User.objects.create_user(
                    email=email,
                    password=validated_data['password'],
                    tenant=tenant,
                    staff_profile=staff,
                    role='Admin',
                    first_name=validated_data.get('first_name', ''),
                    last_name=validated_data.get('last_name', '')
                )
                logger.info(f"Admin user created successfully: {email} (ID: {user.user_id})")
                
                logger.info(f"Tenant provisioning completed successfully for: {business_name}")
                return tenant
                
        except Exception as e:
            # Log the full traceback for debugging
            logger.error(
                f"Tenant provisioning failed for {business_name} ({email}): {str(e)}",
                exc_info=True
            )
            raise
