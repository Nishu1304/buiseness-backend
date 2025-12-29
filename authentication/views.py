import logging
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import CustomTokenObtainPairSerializer, TenantProvisioningSerializer

# Initialize logger for this module
logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login endpoint that returns JWT tokens with custom claims.
    
    Extends the default TokenObtainPairView to use our CustomTokenObtainPairSerializer
    which adds tenant_id and role claims to the access token.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """
        Handle login requests.
        
        Args:
            request: HTTP request containing email and password
            
        Returns:
            Response with access and refresh tokens on success
        """
        try:
            logger.info(f"Login attempt for email: {request.data.get('email', 'unknown')}")
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                logger.info(f"Login successful for email: {request.data.get('email')}")
            else:
                logger.warning(f"Login failed for email: {request.data.get('email')} - Status: {response.status_code}")
                
            return response
            
        except Exception as e:
            logger.error(f"Login error for email {request.data.get('email', 'unknown')}: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred during login. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class LogoutAndBlacklistRefreshTokenForUserView(APIView):
    """
    Logout endpoint that blacklists a refresh token.
    
    When a user logs out, their refresh token is added to a blacklist
    to prevent it from being used to generate new access tokens.
    This is a security best practice.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        """
        Blacklist the provided refresh token.
        
        Args:
            request: HTTP request containing the refresh token to blacklist
            
        Returns:
            205 Reset Content on success
            400 Bad Request if token is invalid or missing
        """
        refresh_token = request.data.get("refresh")
        
        # Validate that refresh token is provided
        if not refresh_token:
            logger.warning(f"Logout attempt without refresh token by user: {request.user.email}")
            return Response(
                {"detail": "Refresh token required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create RefreshToken instance and blacklist it
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User logged out successfully: {request.user.email}")
            return Response(status=status.HTTP_205_RESET_CONTENT)
            
        except TokenError as e:
            # Token is invalid, expired, or already blacklisted
            logger.warning(f"Invalid token during logout for user {request.user.email}: {str(e)}")
            return Response(
                {"detail": "Invalid or expired token"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Logout error for user {request.user.email}: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred during logout"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class TenantProvisioningView(APIView):
    """
    Internal endpoint for creating new tenants (Admin only).
    
    This endpoint is protected by IsAdminUser permission, meaning only
    Django superusers can access it. It's used to onboard new clients
    by creating their Tenant, initial Admin User, and Staff profile.
    """
    permission_classes = (permissions.IsAdminUser,)

    def post(self, request):
        """
        Create a new tenant with an admin user.
        
        Args:
            request: HTTP request containing tenant and admin user details
            
        Returns:
            201 Created with tenant details on success
            400 Bad Request if validation fails
        """
        try:
            logger.info(f"Tenant provisioning request by superuser: {request.user.email}")
            
            # Validate and serialize the request data
            serializer = TenantProvisioningSerializer(data=request.data)
            
            if serializer.is_valid():
                # Create the tenant (this also creates Staff and User)
                tenant = serializer.save()
                
                logger.info(f"Tenant provisioning successful: {tenant.business_name} (ID: {tenant.tenant_id})")
                
                return Response({
                    "message": "Tenant and Admin User created successfully.",
                    "tenant_id": tenant.tenant_id,
                    "business_name": tenant.business_name
                }, status=status.HTTP_201_CREATED)
            
            # Validation failed
            logger.warning(f"Tenant provisioning validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            # Catch any unexpected errors during provisioning
            logger.error(f"Tenant provisioning error: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An error occurred while creating the tenant. Please check logs."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Example commented code for future reference
# class ProductViewSet(ModelViewSet):
#     """
#     Example ViewSet showing how to filter by tenant_id from JWT token.
#     """
#     def get_queryset(self):
#         # Extract tenant_id from the JWT token claims
#         tenant_id = self.request.auth.get("tenant_id")
#         # Filter products by tenant to ensure data isolation
#         return Product.objects.filter(tenant_id=tenant_id)
