# Database Reset & Admin Setup - Complete Guide

## 📦 Files Created

1. **reset_db.ps1** - Automated database reset script
2. **create_test_data.py** - Test data generation script
3. **reset_database.md** - Manual reset instructions

## 🚀 Quick Start - Reset Database

### Step 1: Stop the Server
Press `Ctrl+C` in the terminal running `python manage.py runserver`

### Step 2: Run Reset Script
```powershell
cd d:\Projects\BOS\business-backend
.\reset_db.ps1
```

This will:
- ✅ Delete the database
- ✅ Delete all migration files
- ✅ Create fresh migrations
- ✅ Apply migrations
- ✅ Prompt you to create a superuser

### Step 3: Create Test Data (Optional)
```bash
python manage.py shell
```

Then paste:
```python
exec(open('create_test_data.py').read())
```

This creates:
- 1 Tenant (ABC Electronics Store)
- 2 Users (admin@abc.com, staff@abc.com)
- 3 Categories (Electronics, Clothing, Food & Beverages)
- 3 Sample Products

### Step 4: Start Server
```bash
python manage.py runserver
```

### Step 5: Access Admin Panel
Go to: **http://localhost:8000/admin**

Login with:
- **Superuser**: (email/password you created in Step 2)
- **OR Test Admin**: admin@abc.com / admin123 (if you ran test data script)

## 📋 Models Registered in Admin

All models are already registered! You'll see:

### Authentication App
- ✅ **Tenants** - Manage client organizations
- ✅ **Users** - Manage user accounts

### Inventory App
- ✅ **Categories** - Product categories
- ✅ **Products** - Product catalog
- ✅ **Product Images** - Product photos
- ✅ **Stock Movements** - Inventory tracking

## 🔑 Test Credentials (After Running Test Data Script)

### Admin User
- Email: `admin@abc.com`
- Password: `admin123`
- Tenant: ABC Electronics Store
- Role: Admin

### Staff User
- Email: `staff@abc.com`
- Password: `staff123`
- Tenant: ABC Electronics Store
- Role: Staff

## 🧪 Testing the API

### Option 1: Postman
1. Import: `inventory/Inventory_API_Postman_Collection.json`
2. Update login credentials in "Login (Get Token)" request
3. Run requests in order

### Option 2: PowerShell Script
```powershell
cd inventory
.\test_api_endpoints.ps1
```

## 📝 Admin Panel Features

### Tenant Management
- View all tenants
- Create new tenants
- Edit tenant details (plan, status, subscription)

### User Management
- Create users with tenant assignment
- Assign roles (Admin/Staff)
- Link to staff profiles (if using HR module)

### Category Management
- Create/edit categories
- Filter by tenant
- Search by name

### Product Management
- Full product CRUD
- Upload product images (inline)
- View stock levels
- Filter by category, tenant, status
- Search by name, SKU, brand

### Stock Movement Tracking
- View all stock movements
- Filter by type (IN, OUT, SALE, RETURN)
- Filter by product or tenant
- Read-only (created automatically)

## ⚠️ Important Notes

1. **Always assign tenants to users** - Users without tenants will get permission errors
2. **Stock is read-only in admin** - Use API endpoints to add/remove stock
3. **Categories must belong to the same tenant as products**
4. **Superusers can see all data** - Regular users only see their tenant's data

## 🐛 Troubleshooting

### "Permission denied" errors
- Check if user has a tenant assigned
- Verify user is authenticated
- See: `PERMISSION_ISSUES_EXPLAINED.md`

### Migration errors
- Delete `db.sqlite3`
- Delete all `0*.py` files in `*/migrations/` folders
- Run `python manage.py makemigrations`
- Run `python manage.py migrate`

### Can't login to admin
- Make sure you created a superuser
- Use email (not username) to login
- Check password is correct

## 📚 Additional Documentation

- **API Documentation**: `inventory/API_DOCUMENTATION.md`
- **Postman Collection**: `inventory/Inventory_API_Postman_Collection.json`
- **Permission Issues**: `inventory/PERMISSION_ISSUES_EXPLAINED.md`
- **Test Script**: `inventory/test_api_endpoints.ps1`
