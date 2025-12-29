from django.db import models
from authentication.models import Tenant
from core.managers import TenantManager

class Category(models.Model):
    category_id = models.BigAutoField(primary_key=True)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE,
        related_name='categories',
        db_index=True,
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length = 50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        #ensures two tenants can have same category 
        #but same category name cannot be used by same tenant
        unique_together = ('tenant', 'name')
        ordering = ['name'] 

    def __str__(self):
        return f"{self.name} ({self.tenant.business_name})"


class Product(models.Model):
    product_id = models.BigAutoField(primary_key=True)
    
    #-------------tenant relationship-------------
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
    )

    #-------------category relationship-------------
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE,
        related_name='products',
        db_index=True,
    )

    #-------------sub category relationship-------------
    #not implemnented
    # subcategory = models.ForeignKey(
    #     Category, 
    #     on_delete=models.SET_NULL,
    #     related_name='products',
    #     db_index=True,
    #     null=True,
    #     blank=True
    # )

    #-------------basic product info-------------
    name = models.CharField(max_length=255)
    sku  =  models.CharField(max_length=100)
    brand = models.CharField(max_length=100, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, default='pcs', help_text="Unit of measurement (pcs, box, kg, litre, etc.)")

    #-------------pricing-------------------------
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    #discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)    
    
    #-------------stock-------------------------
    current_stock = models.IntegerField(default=0)
    low_stock_alert = models.IntegerField(default=0)

    #--------------tax--------------------------
    hsn_code = models.CharField(max_length=100, blank=True, null=True)
    gst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    #-------------status------------------------
    status = models.CharField(max_length = 50, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    

    objects = TenantManager()

    class Meta:
        unique_together = ('tenant', 'sku')
        ordering = ['name'] 
        indexes =[
            models.Index(fields=['tenant']),
            models.Index(fields=['sku'])
        ]

    def __str__(self):
        return f"{self.name} - {self.sku} "

class ProductImage(models.Model):
    image_id = models.BigAutoField(primary_key=True)
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='images',
        db_index=True,
    )

    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()

    def __str__(self):
        return f"Image for{self.product.name}"

class StockMovement(models.Model):
    movement_id = models.BigAutoField(primary_key=True)
    
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE,
        related_name='stock_movements',
        db_index=True,
    )

    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        related_name='movements',
        db_index=True,
    )

    MOVEMENT_TYPES = (
        ("IN", "Stock In"),
        ("OUT", "Stock Out"),
        ("SALE", "Stock Deducted for Sale"),
        ("RETURN", "Stock Added for Return"),
    )

    type = models.CharField(max_length=10, choices=MOVEMENT_TYPES) 

    quantity = models.IntegerField()
    
    reference_type = models.CharField(
        max_length=100,
        blank = True,
        null = True,
        help_text = "Bill, Manual Adjustment, Purchase Order, etc."
        )

    reason = models.TextField(blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-date']  

    def __str__(self):
        return f"{self.type} - {self.quantity} of {self.product.name}"