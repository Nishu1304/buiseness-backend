# Database Reset Guide

## Steps to Clear Database and Start Fresh

### 1. Stop the Django Server
Press `Ctrl+C` in the terminal running the server.

### 2. Delete the Database File
```powershell
# Delete SQLite database
Remove-Item db.sqlite3
```

### 3. Delete All Migration Files (except __init__.py)
```powershell
# Delete migration files in all apps
Get-ChildItem -Path . -Recurse -Filter "*.py" -Include "0*.py" | Where-Object { $_.DirectoryName -like "*migrations*" } | Remove-Item -Force

# Or manually delete migration files in:
# - authentication/migrations/0*.py
# - inventory/migrations/0*.py
# - core/migrations/0*.py (if exists)
```

### 4. Create Fresh Migrations
```bash
python manage.py makemigrations
```

### 5. Apply Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser
```bash
python manage.py createsuperuser
# Enter email and password when prompted
```

### 7. Create Test Data (Optional)
Run the Django shell to create a tenant and test user:
```bash
python manage.py shell
```

Then paste:
```python
from authentication.models import Tenant, User
from datetime import datetime, timedelta

# Create a tenant
tenant = Tenant.objects.create(
    business_name="Test Business",
    plan="Standard",
    status="Active",
    sub_end_date=datetime.now() + timedelta(days=365)
)
print(f"✓ Created tenant: {tenant.business_name}")

# Create a tenant user
user = User.objects.create_user(
    email="tenant@example.com",
    password="password123",
    tenant=tenant,
    role="Admin"
)
print(f"✓ Created user: {user.email}")
print(f"  Password: password123")
print(f"  Tenant: {tenant.business_name}")
```

### 8. Start the Server
```bash
python manage.py runserver
```

### 9. Access Admin Panel
Go to: http://localhost:8000/admin
Login with your superuser credentials.

## Quick Reset Script (PowerShell)

Save this as `reset_db.ps1`:

```powershell
# Stop server (if running)
Write-Host "Step 1: Make sure Django server is stopped (Ctrl+C)" -ForegroundColor Yellow
Read-Host "Press Enter when ready"

# Delete database
Write-Host "`nStep 2: Deleting database..." -ForegroundColor Cyan
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "✓ Database deleted" -ForegroundColor Green
} else {
    Write-Host "No database file found" -ForegroundColor Yellow
}

# Delete migrations
Write-Host "`nStep 3: Deleting migration files..." -ForegroundColor Cyan
Get-ChildItem -Path . -Recurse -Filter "*.py" -Include "0*.py" | Where-Object { $_.DirectoryName -like "*migrations*" } | Remove-Item -Force
Write-Host "✓ Migration files deleted" -ForegroundColor Green

# Make migrations
Write-Host "`nStep 4: Creating fresh migrations..." -ForegroundColor Cyan
python manage.py makemigrations

# Migrate
Write-Host "`nStep 5: Applying migrations..." -ForegroundColor Cyan
python manage.py migrate

# Create superuser
Write-Host "`nStep 6: Create superuser" -ForegroundColor Cyan
python manage.py createsuperuser

Write-Host "`n✓ Database reset complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Run: python manage.py runserver"
Write-Host "  2. Access admin: http://localhost:8000/admin"
```

Run it with:
```powershell
.\reset_db.ps1
```
