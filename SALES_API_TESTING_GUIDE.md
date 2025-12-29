# Sales API - Postman Collection Guide

## Overview

This Postman collection provides comprehensive testing for the Sales API module, including:
- Authentication (Login, Token Refresh, Logout)
- Customer Management (CRUD operations)
- Bill Creation and Management
- Payment Processing
- Error Scenario Testing

## Setup Instructions

### 1. Import the Collection

1. Open Postman
2. Click **Import** button
3. Select the file: `Sales_API_Postman_Collection.json`
4. The collection will be imported with all requests organized in folders

### 2. Configure Variables

The collection uses the following variables (automatically managed):

| Variable | Description | Default Value |
|----------|-------------|---------------|
| `base_url` | API base URL | `http://localhost:8000` |
| `access_token` | JWT access token | Auto-populated on login |
| `refresh_token` | JWT refresh token | Auto-populated on login |
| `customer_id` | Created customer ID | Auto-populated |
| `bill_id` | Created bill ID | Auto-populated |
| `payment_id` | Created payment ID | Auto-populated |
| `product_id` | Product ID for testing | **Manual setup required** |

### 3. Before Testing

#### Step 1: Start the Django Server
```bash
cd d:\Projects\BOS\business-backend
python manage.py runserver
```

#### Step 2: Create Test Data

You need to have:
1. **A tenant user account** - Use the login credentials
2. **At least one product** - Get the product_id from inventory API

To set the `product_id` variable:
1. Go to the collection variables
2. Set `product_id` to an existing product ID from your database
3. Or use the Inventory API to create a product first

## Testing Workflow

### Recommended Testing Order

#### 1. Authentication Flow
```
1. Login (Get Token)
   └─> Saves access_token and refresh_token automatically
2. Refresh Token (when access token expires)
3. Logout (when done testing)
```

#### 2. Customer Management Flow
```
1. Create Customer
   └─> Saves customer_id automatically
2. List All Customers
3. Get Customer Details
4. Update Customer (PUT - full update)
5. Partial Update Customer (PATCH - partial update)
6. Delete Customer (cleanup)
```

#### 3. Bill Creation Flow
```
Prerequisites: 
- Have a valid customer_id
- Have a valid product_id with sufficient stock

1. Create Bill (Cash Sale)
   └─> Saves bill_id automatically
   └─> Deducts stock from product
   └─> Creates stock movement record

2. Create Bill (Credit Sale)
   └─> Increases customer spending_balance
   └─> Deducts stock from product

3. Create Bill (Without Customer)
   └─> For walk-in customers

4. Get Bill Details
   └─> View bill with all items and calculations
```

#### 4. Payment Processing Flow
```
Prerequisites:
- Have a customer with credit balance (create a credit sale first)

1. Create Payment (Customer Paying)
   └─> Type: CREDIT
   └─> Reduces customer spending_balance

2. Create Payment (Debit)
   └─> Type: DEBIT
   └─> Increases customer spending_balance

3. List All Payments
4. Get Payment Details
5. Update Payment
6. Delete Payment
```

#### 5. Error Scenarios Testing
```
Test the following error cases:
1. Insufficient Stock - Try to sell more than available
2. Negative Payment Amount - Should fail validation
3. Zero Payment Amount - Should fail validation
4. Invalid Product ID - Product doesn't exist
5. Bill with No Items - Should fail validation
```

## Request Details

### Authentication Requests

#### Login
- **Method**: POST
- **Endpoint**: `/api/token/`
- **Auth**: None
- **Body**:
  ```json
  {
    "email": "tenant@example.com",
    "password": "your_password"
  }
  ```
- **Response**: Returns `access` and `refresh` tokens
- **Auto-saves**: Both tokens to collection variables

#### Refresh Token
- **Method**: POST
- **Endpoint**: `/api/token/refresh/`
- **Body**:
  ```json
  {
    "refresh": "{{refresh_token}}"
  }
  ```

### Customer Requests

#### Create Customer
- **Method**: POST
- **Endpoint**: `/api/sales/customers/`
- **Auth**: Bearer Token (automatic)
- **Body**:
  ```json
  {
    "name": "John Doe",
    "phone": "+91-9876543210",
    "email": "john.doe@example.com",
    "gst_number": "29ABCDE1234F1Z5",
    "type": "Regular"
  }
  ```

### Bill Requests

#### Create Bill
- **Method**: POST
- **Endpoint**: `/api/sales/bills/`
- **Auth**: Bearer Token (automatic)
- **Body**:
  ```json
  {
    "customer_id": 1,
    "bill_discount": 50.00,
    "payment_type": "CASH",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "price": 500.00,
        "discount": 10.00
      }
    ]
  }
  ```

**Important Notes**:
- `customer_id` is optional (for walk-in customers)
- `price` is optional (defaults to product's selling_price)
- `discount` is per-unit discount
- Stock is automatically deducted
- GST is automatically calculated
- Stock movement records are created

### Payment Requests

#### Create Payment
- **Method**: POST
- **Endpoint**: `/api/sales/payments/`
- **Auth**: Bearer Token (automatic)
- **Body**:
  ```json
  {
    "customer": 1,
    "amount": 1000.00,
    "type": "CREDIT"
  }
  ```

**Payment Types**:
- `CREDIT`: Customer paying back (reduces spending_balance)
- `DEBIT`: Additional charge (increases spending_balance)

## Validation Rules

### Customer Validation
- ✅ Name is required
- ✅ Phone, email, GST number are optional
- ✅ Type defaults to "Regular"
- ✅ Spending balance is read-only

### Bill Validation
- ✅ Must have at least one item
- ✅ All products must exist and belong to tenant
- ✅ Sufficient stock must be available
- ✅ Quantity must be > 0
- ✅ Totals are auto-calculated

### Payment Validation
- ✅ Amount must be > 0
- ✅ Customer must belong to the tenant
- ✅ Type must be CREDIT or DEBIT

## Expected Responses

### Success Responses

#### Customer Created (201)
```json
{
  "customer_id": 1,
  "name": "John Doe",
  "phone": "+91-9876543210",
  "email": "john.doe@example.com",
  "gst_number": "29ABCDE1234F1Z5",
  "type": "Regular",
  "spending_balance": "0.00",
  "created_at": "2025-12-09T07:30:00Z"
}
```

#### Bill Created (201)
```json
{
  "bill_id": 1,
  "date": "2025-12-09T07:35:00Z",
  "customer": 1,
  "customer_name": "John Doe",
  "created_by": null,
  "item_total": "1280.00",
  "bill_discount": "50.00",
  "gst_total": "221.40",
  "grand_total": "1451.40",
  "payment_type": "CASH",
  "items": [
    {
      "bill_item_id": 1,
      "product": 1,
      "product_name": "Sample Product",
      "quantity": 2,
      "price": "500.00",
      "discount": "10.00",
      "subtotal": "980.00"
    }
  ]
}
```

### Error Responses

#### Insufficient Stock (400)
```json
{
  "error": "Insufficient stock for product Sample Product"
}
```

#### Invalid Payment Amount (400)
```json
{
  "amount": ["Payment amount must be greater than zero."]
}
```

#### Unauthorized (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Tips for Testing

### 1. Sequential Testing
- Always login first to get tokens
- Create customers before creating bills
- Create products in inventory before testing bills
- Check customer spending_balance after credit sales

### 2. Monitoring Changes
After creating a bill, check:
- Product stock levels (should decrease)
- Stock movement records (should be created)
- Customer spending_balance (if credit sale)

### 3. Testing Edge Cases
Use the "Error Scenarios" folder to test:
- Validation errors
- Business logic errors
- Authorization errors

### 4. Token Expiration
- Access tokens expire after 15 minutes
- Use "Refresh Token" request to get a new access token
- Or login again to get fresh tokens

## Troubleshooting

### "Authentication credentials were not provided"
- Ensure you've logged in and the access_token is set
- Check if token has expired (refresh or login again)

### "Product not found or not in tenant"
- Verify the product_id exists
- Ensure the product belongs to your tenant
- Create a product using Inventory API first

### "Insufficient stock"
- Check product's current_stock
- Reduce quantity in bill items
- Add stock using Inventory API

### "Customer does not belong to your tenant"
- Ensure you're using the correct customer_id
- Customer must be created by the same tenant

## Collection Variables Reference

To view/edit collection variables:
1. Click on the collection name
2. Go to "Variables" tab
3. View or edit the "Current Value" column

## Next Steps

After testing the Sales API:
1. Test integration with Inventory API
2. Verify stock movements are created correctly
3. Test multi-tenant isolation
4. Create automated test scripts
5. Set up environment variables for different environments (dev, staging, prod)

## Support

For issues or questions:
- Check the walkthrough document for bug fixes
- Review Django server logs for detailed error messages
- Verify database state using Django admin panel
