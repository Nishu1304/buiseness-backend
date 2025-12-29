
1. Changes Implemented
Models:
Tenant (authentication/models.py): Created with fields business_name, plan, status, etc.
User (authentication/models.py): Custom user model extending AbstractUser.
Replaced username with email as the unique identifier.
Added tenant (ForeignKey to Tenant).
Added role (Admin/Staff).
Added staff_profile (ForeignKey to Staff).
Staff (hr/models.py): Created in a new hr app to match the "HR & Operations" domain. Linked to Tenant.
Configuration:
Renamed the local auth app to authentication to avoid conflict with Django's built-in auth.
Updated settings.py to use authentication.User as the AUTH_USER_MODEL.
Added hr and authentication to INSTALLED_APPS.
Views & URLs:
Wired CustomTokenObtainPairView to /api/token/.
Wired LogoutAndBlacklistRefreshTokenForUserView to /api/auth/logout/.
2. How Authentication Works Now
Registration/Setup (Manual for now): You need to create a Tenant and a User (linked to that tenant) via Django Admin or shell.
Login:
Send POST to /api/token/ with email and password.
Response: Access Token + Refresh Token.
Payload: The Access Token contains custom claims:
user_id: The user's primary key.
tenant_id: The ID of the tenant the user belongs to.
role: The user's role (Admin/Staff).
Accessing Resources:
Send the Access Token in the Authorization header: Bearer <access_token>.
The TenantFromJWTMiddleware (if active) or IsTenantMember permission can now reliably read tenant_id from the token to enforce data isolation.
Logout:
Send POST to /api/auth/logout/ with refresh_token.
The refresh token is blacklisted, preventing further access token generation.
Next Steps:

You might want to create a "Registration" endpoint to allow new tenants to sign up.
You can now proceed with building the other modules (Inventory, Sales) using tenant_id for isolation.