from django.db import transaction
from django.db.models import F
from decimal import Decimal
from inventory.models import Product, StockMovement
from .models import Bill, BillItem, Customer


class InsufficientStock(Exception):
    pass


def create_bill(tenant, created_by_staff, payload):
    """
    payload = {
        "customer_id": <optional>,
        "bill_discount": Decimal or float,
        "payment_type": "CASH" / "CREDIT" / ...
        "items": [
            {"product_id": id, "quantity": int, "price": Decimal, "discount": Decimal (per-unit)},
            ...
        ]
    }
    """
    items = payload.get("items", [])
    if not items:
        raise ValueError("Bill must contain at least one item.")

    with transaction.atomic():
        customer = None
        if payload.get("customer_id"):
            customer = Customer.objects.select_for_update().get(pk=payload["customer_id"], tenant=tenant)

        # create bill skeleton
        bill = Bill.objects.create(
            tenant=tenant,
            customer=customer,
            created_by=created_by_staff,
            bill_discount=Decimal(payload.get("bill_discount", 0)),
            payment_type=payload.get("payment_type")
        )

        # process each item
        for it in items:
            product = Product.objects.select_for_update().get(pk=it["product_id"], tenant=tenant)

            qty = int(it["quantity"])
            if qty <= 0:
                raise ValueError("Quantity must be > 0")

            if product.current_stock < qty:
                raise InsufficientStock(f"Insufficient stock for product {product.name}")

            price = Decimal(it.get("price", product.selling_price))
            discount = Decimal(it.get("discount", 0))
            subtotal = (price - discount) * qty

            bill_item = BillItem.objects.create(
                bill=bill,
                product=product,
                quantity=qty,
                price=price,
                discount=discount,
                subtotal=subtotal
            )

            # update product stock
            product.current_stock = F('current_stock') - qty
            product.save(update_fields=['current_stock'])

            # create stock movement record
            StockMovement.objects.create(
                tenant=tenant,
                product=product,
                type="SALE",
                quantity=qty,
                reference_type="Bill",
                reason=f"Sale - Bill {bill.bill_id}"
            )

        # reload product rows so F() evaluated
        # (optional) recalc totals
        bill = Bill.objects.select_for_update().get(pk=bill.pk)
        bill.recalculate_totals()
        bill.save()

        # update customer spending_balance
        if customer:
            # increase spending_balance by grand_total if payment_type indicates credit, else maybe no change
            # Here we assume spending_balance increases on credit sale; change per your business logic
            if payload.get("payment_type") and payload.get("payment_type").upper() == "CREDIT":
                customer.spending_balance = F('spending_balance') + bill.grand_total
                customer.save(update_fields=['spending_balance'])

        return bill
