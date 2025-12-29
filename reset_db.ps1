# ============================================
# Database Reset Script (PowerShell)
# ============================================
# This script will:
# 1. Delete the database
# 2. Delete all migration files
# 3. Create fresh migrations
# 4. Apply migrations
# 5. Prompt to create superuser

Write-Host "`n=========================================="  -ForegroundColor Cyan
Write-Host "DATABASE RESET SCRIPT" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Check if server is running
Write-Host "`n⚠️  WARNING: Make sure Django server is stopped!" -ForegroundColor Yellow
Write-Host "Press Ctrl+C in the server terminal if it's running." -ForegroundColor Yellow
$continue = Read-Host "`nContinue with database reset? (yes/no)"

if ($continue -ne "yes") {
    Write-Host "❌ Aborted" -ForegroundColor Red
    exit
}

# Step 2: Delete database
Write-Host "`n[1/5] Deleting database..." -ForegroundColor Cyan
if (Test-Path "db.sqlite3") {
    Remove-Item "db.sqlite3" -Force
    Write-Host "✓ Database deleted" -ForegroundColor Green
}
else {
    Write-Host "⚠️  No database file found (already clean)" -ForegroundColor Yellow
}

# Step 3: Delete migration files
Write-Host "`n[2/5] Deleting migration files..." -ForegroundColor Cyan
$migrationFiles = Get-ChildItem -Path . -Recurse -Filter "*.py" | Where-Object { 
    $_.DirectoryName -like "*migrations*" -and $_.Name -match "^\d{4}_.*\.py$"
}

if ($migrationFiles.Count -gt 0) {
    $migrationFiles | Remove-Item -Force
    Write-Host "✓ Deleted $($migrationFiles.Count) migration files" -ForegroundColor Green
}
else {
    Write-Host "⚠️  No migration files found" -ForegroundColor Yellow
}

# Step 4: Create fresh migrations
Write-Host "`n[3/5] Creating fresh migrations..." -ForegroundColor Cyan
python manage.py makemigrations
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migrations created" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to create migrations" -ForegroundColor Red
    exit 1
}

# Step 5: Apply migrations
Write-Host "`n[4/5] Applying migrations..." -ForegroundColor Cyan
python manage.py migrate
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migrations applied" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to apply migrations" -ForegroundColor Red
    exit 1
}

# Step 6: Create superuser
Write-Host "`n[5/5] Create superuser" -ForegroundColor Cyan
Write-Host "You will be prompted to enter email and password..." -ForegroundColor Yellow
python manage.py createsuperuser

# Summary
Write-Host "`n=========================================="  -ForegroundColor Green
Write-Host "✓ DATABASE RESET COMPLETE!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "`n📋 What was done:" -ForegroundColor Cyan
Write-Host "  ✓ Database deleted and recreated"
Write-Host "  ✓ All migrations reset"
Write-Host "  ✓ Superuser created"

Write-Host "`n📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Start server: python manage.py runserver"
Write-Host "  2. Access admin: http://localhost:8000/admin"
Write-Host "  3. Create a Tenant in admin panel"
Write-Host "  4. Create a User and assign the tenant"
Write-Host "  5. Test API with Postman collection"

Write-Host "`n💡 Quick Test Data Creation:" -ForegroundColor Cyan
Write-Host "Run: python manage.py shell"
Write-Host "Then paste the code from: create_test_data.py"
Write-Host ""
