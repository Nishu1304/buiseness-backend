from django.contrib import admin
from sales.models import Customer, CustomerPayment, Bill, BillItem
# Register your models here.


admin.site.register(Customer)
admin.site.register(CustomerPayment)
admin.site.register(BillItem)
admin.site.register(Bill)

