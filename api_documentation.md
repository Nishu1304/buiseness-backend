# API Documentation - BOS Backend

## Overview
This document describes all the authentication APIs available in the BOS (Business Operations System) backend. The system uses JWT (JSON Web Token) authentication with custom claims for multi-tenancy support.

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant Admin as Super Admin
    participant System as BOS API
    participant DB as Database
    
    Admin->>System: 1. Create Superuser (CLI)
    Admin->>System: 2. Login (POST /api/token/)
    System->>DB: Verify credentials
    System->>Admin: Access + Refresh Tokens
    Admin->>System: 3. Provision Tenant (with Access Token)
    System->>DB: Create Tenant, User, Staff
    System->>Admin: Success Response
    
    participant Client as Tenant User
    Client->>System: 4. Login (POST /api/token/)
    System->>DB: Verify credentials
    System->>Client: Access + Refresh Tokens (with tenant_id)
    Client->>System: 5. Access Resources (with Access Token)
    System->>Client: Protected Data
    Client->>System: 6. Logout (POST /api/auth/logout/)
    System->>DB: Blacklist Refresh Token
```

---

## API Endpoints

### 1. Login (Token Obtain Pair)

**Endpoint:** `POST /api/token/`

**Purpose:** Authenticate users and obtain JWT access and refresh tokens.

**Authentication:** None (Public)

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response (Success - 200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Access Token Payload:**
```json
{
  "token_type": "access",
  "exp": 1701234567,
  "iat": 1701233667,
  "jti": "abc123...",
  "user_id": 1,
  "tenant_id": 5,
  "role": "Admin"
}
```

**How It Works:**
1. The user submits their email and password.
2. Django authenticates using the custom [User](file:///d:/Projects/BOS/backend/authentication/models.py#32-47) model (email-based).
3. If valid, [CustomTokenObtainPairSerializer](file:///d:/Projects/BOS/backend/authentication/serializers.py#3-18) generates JWT tokens with custom claims:
   - `user_id`: The user's primary key
   - `tenant_id`: Extracted from `user.tenant_id` or `user.staff_profile.tenant_id`
   - `role`: The user's role (Admin/Staff)
4. Access token expires in **15 minutes**, refresh token in **7 days**.

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "password123"}'
```

**Common Errors:**
- **401 Unauthorized:** Invalid email or password
- **400 Bad Request:** Missing email or password fields

---

### 2. Refresh Token

**Endpoint:** `POST /api/token/refresh/`

**Purpose:** Obtain a new access token using a valid refresh token.

**Authentication:** None (requires valid refresh token)

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Success - 200):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**How It Works:**
1. The client sends their refresh token.
2. If valid and not blacklisted, a new access token is generated.
3. Due to `ROTATE_REFRESH_TOKENS: True`, a new refresh token is also issued.
4. The old refresh token is blacklisted (due to `BLACKLIST_AFTER_ROTATION: True`).

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

**Common Errors:**
- **401 Unauthorized:** Refresh token is invalid, expired, or blacklisted

---

### 3. Logout (Blacklist Refresh Token)

**Endpoint:** `POST /api/auth/logout/`

**Purpose:** Invalidate a refresh token to log out the user.

**Authentication:** Required (Bearer Token)

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Request Body:**
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (Success - 205):**
```
HTTP 205 Reset Content
```

**How It Works:**
1. The client sends their refresh token in the request body.
2. The API verifies the user is authenticated (via access token in header).
3. The refresh token is blacklisted in the database.
4. Future attempts to use this refresh token will fail.

**Example (cURL):**
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

**Common Errors:**
- **401 Unauthorized:** Access token missing or invalid
- **400 Bad Request:** Refresh token missing or invalid format

---

### 4. Provision Tenant (Internal Only)

**Endpoint:** `POST /api/internal/provision-tenant/`

**Purpose:** Create a new tenant and their initial admin user (Internal use only).

**Authentication:** Required (Super Admin only - `IsAdminUser`)

**Headers:**
```
Authorization: Bearer YOUR_SUPERUSER_ACCESS_TOKEN
```

**Request Body:**
```json
{
  "business_name": "Acme Corporation",
  "plan": "Standard",
  "email": "admin@acme.com",
  "password": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "1234567890"
}
```

**Fields:**
- `business_name` (required): Name of the tenant's business
- `plan` (required): Subscription plan - `"Basic"` or `"Standard"`
- [email](file:///d:/Projects/BOS/backend/authentication/serializers.py#33-37) (required): Email for the tenant's admin user
- `password` (required): Password for the admin user
- `first_name` (optional): Admin's first name
- `last_name` (optional): Admin's last name
- `phone` (optional): Admin's phone number

**Response (Success - 201):**
```json
{
  "message": "Tenant and Admin User created successfully.",
  "tenant_id": 5,
  "business_name": "Acme Corporation"
}
```

**How It Works:**
1. Checks that the requester is a superuser (Django `is_staff=True`).
2. Creates a [Tenant](file:///d:/Projects/BOS/backend/authentication/models.py#4-14) record with:
   - `business_name`, `plan`
   - `status`: "Active"
   - `sub_end_date`: 30 days from now
3. Creates a [Staff](file:///d:/Projects/BOS/backend/hr/models.py#3-14) profile linked to the tenant.
4. Creates a [User](file:///d:/Projects/BOS/backend/authentication/models.py#32-47) linked to both the tenant and staff profile with role "Admin".
5. The new admin can now log in using their email and password.

**Example (cURL):**
```bash
# First, create a superuser
python manage.py createsuperuser

# Get superuser token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "superadmin@example.com", "password": "admin123"}'

# Provision tenant
curl -X POST http://localhost:8000/api/internal/provision-tenant/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPERUSER_TOKEN" \
  -d '{
    "business_name": "Tech Startup Inc",
    "plan": "Standard",
    "email": "ceo@techstartup.com",
    "password": "StartupPass123",
    "first_name": "Jane",
    "last_name": "Smith",
    "phone": "5551234567"
  }'
```

**Common Errors:**
- **401 Unauthorized:** Missing or invalid access token
- **403 Forbidden:** User is not a superuser
- **400 Bad Request:** 
  - Email already exists
  - Invalid plan choice
  - Missing required fields

---

## Security Features

### Token Lifetimes
- **Access Token:** 15 minutes
- **Refresh Token:** 7 days

### Token Rotation
- When you refresh an access token, you get a **new refresh token**.
- The old refresh token is **blacklisted** and cannot be reused.
- This prevents token replay attacks.

### Custom Claims
All access tokens include:
- `user_id`: For user identification
- `tenant_id`: For data isolation (multi-tenancy)
- `role`: For role-based permissions

### Permissions
- **Public endpoints:** `/api/token/`, `/api/token/refresh/`
- **Authenticated endpoints:** `/api/auth/logout/` (any logged-in user)
- **Admin-only endpoints:** `/api/internal/provision-tenant/` (superuser only)

---

## Getting Started

### 1. Initial Setup
```bash
# Navigate to backend
cd d:/Projects/BOS/backend

# Activate virtual environment
.\venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac

# Create superuser
python manage.py createsuperuser
# Enter email and password when prompted

# Run server
python manage.py runserver
```

### 2. Create Your First Tenant
```bash
# Login as superuser to get token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your_superuser@email.com", "password": "your_password"}'

# Use the access token to create a tenant
curl -X POST http://localhost:8000/api/internal/provision-tenant/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "business_name": "My Business",
    "plan": "Basic",
    "email": "admin@mybusiness.com",
    "password": "BusinessPass123",
    "first_name": "Admin",
    "last_name": "User"
  }'
```

### 3. Login as Tenant Admin
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@mybusiness.com", "password": "BusinessPass123"}'

# The response will include tenant_id in the access token payload
```

---

## Testing with Browsable API

Django REST Framework provides a browsable API interface:

1. Open browser and go to `http://localhost:8000/api/token/`
2. You'll see a form to input email and password
3. After getting tokens, go to `http://localhost:8000/api/internal/provision-tenant/`
4. You'll need to authenticate first (top right corner)
5. Use the HTML form to provision tenants

---

## Troubleshooting

### "401 Unauthorized" on login
- Verify the user exists in the database
- Check email and password are correct
- Ensure you're using [email](file:///d:/Projects/BOS/backend/authentication/serializers.py#33-37), not `username`

### "403 Forbidden" on provision-tenant
- Only superusers can access this endpoint
- Create a superuser with `python manage.py createsuperuser`
- Make sure you're using the superuser's token

### "AttributeError: 'User' object has no attribute 'id'"
- This is fixed by the `USER_ID_FIELD: "user_id"` setting
- If you see this, verify [settings.py](file:///d:/Projects/BOS/backend/core/settings.py) has the correct `SIMPLE_JWT` configuration

### Access token expired
- Use the refresh token to get a new access token
- POST to `/api/token/refresh/` with the refresh token
