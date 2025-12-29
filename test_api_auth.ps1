# Quick API Test Script
# This tests if your API authentication is working

$BASE_URL = "http://localhost:8000"

Write-Host "`n=========================================="  -ForegroundColor Cyan
Write-Host "API AUTHENTICATION TEST" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Step 1: Login
Write-Host "`n[1/3] Testing Login..." -ForegroundColor Cyan
$loginBody = @{
    email = "admin@gmail.com"
    password = "1234"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$BASE_URL/api/token/" -Method Post -Body $loginBody -ContentType "application/json"
    $ACCESS_TOKEN = $loginResponse.access
    Write-Host "✓ Login successful!" -ForegroundColor Green
    Write-Host "  Access Token: $($ACCESS_TOKEN.Substring(0, 30))..." -ForegroundColor Gray
} catch {
    Write-Host "✗ Login failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    Write-Host "`nPossible issues:" -ForegroundColor Yellow
    Write-Host "  1. Server not running (python manage.py runserver)"
    Write-Host "  2. Wrong email/password"
    Write-Host "  3. User doesn't exist in database"
    exit 1
}

# Step 2: Test Categories Endpoint
Write-Host "`n[2/3] Testing Categories Endpoint..." -ForegroundColor Cyan
$headers = @{
    "Authorization" = "Bearer $ACCESS_TOKEN"
    "Content-Type" = "application/json"
}

try {
    $categories = Invoke-RestMethod -Uri "$BASE_URL/api/inventory/categories/" -Method Get -Headers $headers
    Write-Host "✓ Categories endpoint working!" -ForegroundColor Green
    Write-Host "  Found $($categories.count) categories" -ForegroundColor Gray
} catch {
    Write-Host "✗ Categories endpoint failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    
    # Check if it's a permission error
    if ($_ -like "*permission*") {
        Write-Host "`n⚠️  PERMISSION ERROR DETECTED" -ForegroundColor Yellow
        Write-Host "  This means the user doesn't have a tenant assigned!" -ForegroundColor Yellow
        Write-Host "`nTo fix:" -ForegroundColor Cyan
        Write-Host "  1. Run: python manage.py shell"
        Write-Host "  2. Paste: exec(open('check_user_tenants.py').read())"
        Write-Host "  3. Assign tenant to user if needed"
    }
    exit 1
}

# Step 3: Create a Test Category
Write-Host "`n[3/3] Testing Create Category..." -ForegroundColor Cyan
$categoryBody = @{
    name = "Test Category $(Get-Date -Format 'HHmmss')"
    description = "Test category created by API test script"
    status = "active"
} | ConvertTo-Json

try {
    $newCategory = Invoke-RestMethod -Uri "$BASE_URL/api/inventory/categories/" -Method Post -Headers $headers -Body $categoryBody
    Write-Host "✓ Create category working!" -ForegroundColor Green
    Write-Host "  Created: $($newCategory.name) (ID: $($newCategory.category_id))" -ForegroundColor Gray
} catch {
    Write-Host "✗ Create category failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
    exit 1
}

# Summary
Write-Host "`n=========================================="  -ForegroundColor Green
Write-Host "✓ ALL TESTS PASSED!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green

Write-Host "`n📋 Summary:" -ForegroundColor Cyan
Write-Host "  ✓ Authentication working"
Write-Host "  ✓ Authorization working"
Write-Host "  ✓ API endpoints accessible"
Write-Host "  ✓ User has proper tenant assignment"

Write-Host "`n💡 For Postman:" -ForegroundColor Yellow
Write-Host "  1. Run 'Login (Get Token)' request first"
Write-Host "  2. Use email: admin@gmail.com"
Write-Host "  3. Use password: 1234"
Write-Host "  4. Token will be auto-saved to {{access_token}}"
Write-Host "  5. All other requests will use it automatically"
Write-Host ""
