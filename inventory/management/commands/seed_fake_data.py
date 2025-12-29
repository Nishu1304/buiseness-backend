from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random

from authentication.models import Tenant, User
from hr.models import Staff, Attendance
from inventory.models import Category, Product, StockMovement
from sales.models import Customer, Bill, BillItem, CustomerPayment


class Command(BaseCommand):
    help = "Seed logical fake data for sneaker business (single tenant)"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Seeding fake data...")

        # -------------------------
        # TENANT
        # -------------------------
        tenant, _ = Tenant.objects.get_or_create(
            business_name="UrbanKicks",
            defaults={
                "plan": "Standard",
                "status": "Active",
                "sub_end_date": timezone.now() + timezone.timedelta(days=365),
            },
        )

        # -------------------------
        # ADMIN USER
        # -------------------------
        admin, _ = User.objects.get_or_create(
            email="admin@urbankicks.com",
            defaults={
                "tenant": tenant,
                "role": "Admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin.set_password("admin123")
        admin.save()

        # -------------------------
        # STAFF
        # -------------------------
        staff_list = []
        for name, position in [
            ("Rohit Sharma", "Store Manager"),
            ("Aman Verma", "Sales Executive"),
            ("Neha Singh", "Cashier"),
        ]:
            staff = Staff.objects.create(
                tenant=tenant,
                name=name,
                position=position,
                phone=f"9{random.randint(100000000,999999999)}",
                salary=Decimal(random.randint(18000, 35000)),
            )
            staff_list.append(staff)

        # Attendance (last 10 days)
        for staff in staff_list:
            for i in range(10):
                Attendance.objects.create(
                    tenant=tenant,
                    staff=staff,
                    date=timezone.now().date() - timezone.timedelta(days=i),
                    status=random.choice(["Present", "Present", "Absent"]),
                )

        # -------------------------
        # CATEGORIES
        # -------------------------
        categories = {}
        for name in ["Running Shoes", "Casual Sneakers", "High Tops", "Sports Shoes"]:
            categories[name] = Category.objects.create(
                tenant=tenant,
                name=name,
                description=f"{name} collection",
            )

        # -------------------------
        # PRODUCTS
        # -------------------------
        products = []

        product_data = [
            ("Nike Air Zoom Pegasus", "RUN001", "Nike", "Running Shoes", 4500, 6999, 18),
            ("Adidas Ultraboost", "RUN002", "Adidas", "Running Shoes", 6000, 9999, 18),
            ("Puma Smash V2", "CAS001", "Puma", "Casual Sneakers", 2500, 3999, 12),
            ("Converse Chuck 70", "HIGH001", "Converse", "High Tops", 4200, 6499, 12),
            ("Jordan 1 Retro", "HIGH002", "Nike", "High Tops", 9000, 15999, 18),
            ("Reebok Flexagon", "SPORT001", "Reebok", "Sports Shoes", 3000, 4999, 12),
        ]

        for name, sku, brand, cat, cost, price, gst in product_data:
            product = Product.objects.create(
                tenant=tenant,
                category=categories[cat],
                name=name,
                sku=sku,
                brand=brand,
                purchase_price=Decimal(cost),
                selling_price=Decimal(price),
                mrp=Decimal(price + 1000),
                gst_percent=gst,
                current_stock=random.randint(20, 60),
                low_stock_alert=5,
            )
            products.append(product)

            StockMovement.objects.create(
                tenant=tenant,
                product=product,
                type="IN",
                quantity=product.current_stock,
                reference_type="Initial Stock",
            )

        # -------------------------
        # CUSTOMERS
        # -------------------------
        customers = []
        for name in [
            "Arjun Mehta",
            "Karan Patel",
            "Sneha Iyer",
            "Rahul Das",
            "Pooja Nair",
        ]:
            customer = Customer.objects.create(
                tenant=tenant,
                name=name,
                phone=f"9{random.randint(100000000,999999999)}",
                type=random.choice(["Regular", "Premium"]),
            )
            customers.append(customer)

        # -------------------------
        # BILLS + ITEMS (PAST PURCHASES)
        # -------------------------
        for _ in range(15):
            customer = random.choice(customers)
            staff = random.choice(staff_list)

            bill = Bill.objects.create(
                tenant=tenant,
                customer=customer,
                created_by=staff,
                payment_type=random.choice(["Cash", "UPI", "Card"]),
            )

            total = Decimal(0)

            for _ in range(random.randint(1, 3)):
                product = random.choice(products)
                qty = random.randint(1, 2)
                price = product.selling_price

                subtotal = price * qty

                BillItem.objects.create(
                    bill=bill,
                    product=product,
                    quantity=qty,
                    price=price,
                    discount=Decimal(0),
                    subtotal=subtotal,
                )

                total += subtotal

                StockMovement.objects.create(
                    tenant=tenant,
                    product=product,
                    type="SALE",
                    quantity=qty,
                    reference_type=f"Bill {bill.bill_id}",
                )

            bill.item_total = total
            bill.recalculate_totals()
            bill.save()

            CustomerPayment.objects.create(
                tenant=tenant,
                customer=customer,
                amount=bill.grand_total,
                type="DEBIT",
            )

        self.stdout.write(self.style.SUCCESS("✅ Fake sneaker business data created successfully"))
