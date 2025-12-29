from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from authentication.models import Tenant
from core.managers import TenantManager
from inventory.models import Product

class Customer(models.Model):
    customer_id = models.BigAutoField(primary_key = True)

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="customers", db_index = True)
    
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    type = models.CharField(max_length=50, default="Regular")
    spending_balance = models.DecimalField(
        max_digits=14, decimal_places=2, default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.tenant.business_name})"


class Bill(models.Model):
    bill_id = models.BigAutoField(primary_key=True)

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="bills", db_index=True
    )

    customer = models.ForeignKey(
        Customer, null=True, blank=True, on_delete=models.SET_NULL, related_name="bills"
    )

    created_by = models.ForeignKey(
        "hr.Staff", null=True, blank=True, on_delete=models.SET_NULL, related_name="bills"
    )

    date = models.DateTimeField(auto_now_add=True)
    item_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    bill_discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gst_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    payment_type = models.CharField(max_length=50, blank=True, null=True)

    objects = TenantManager()

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Bill {self.bill_id} - {self.tenant.business_name}"

    def recalculate_totals(self):
        items = self.items.all()
        item_total = sum([it.subtotal for it in items])
        self.item_total = item_total
        # Simple GST calculation if gst_total not provided; you can change logic
        self.gst_total = sum([
            (getattr(it.product, 'gst_percent', 0) / 100) * (it.price * it.quantity - it.discount * it.quantity) 
            for it in items
        ])
        self.grand_total = self.item_total + self.gst_total - (self.bill_discount or 0)
        return self


class BillItem(models.Model):
    bill_item_id = models.BigAutoField(primary_key=True)
    bill = models.ForeignKey(Bill, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Bill {self.bill.bill_id})"


class CustomerPayment(models.Model):
    payment_id = models.BigAutoField(primary_key=True)

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="payments", db_index=True
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    type = models.CharField(max_length=20, choices=(("CREDIT", "Credit"), ("DEBIT", "Debit")))
    date = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    def __str__(self):
        return f"Payment {self.payment_id} - {self.amount}"