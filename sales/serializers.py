from rest_framework import serializers
from .models import Customer, Bill, BillItem, CustomerPayment
from inventory.serializers import StockMovementSerializer  # optional reuse


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["customer_id", "name", "phone", "email", "gst_number", "type", "spending_balance", "created_at"]
        read_only_fields = ["customer_id", "spending_balance", "created_at"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return Customer.objects.create(tenant=tenant, **validated_data)


class BillItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)


class BillCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False, allow_null=True)
    bill_discount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    payment_type = serializers.CharField(required=False, allow_blank=True)
    items = BillItemInputSerializer(many=True)

    def validate(self, data):
        # You can add tenant checks: confirm all products belong to tenant
        request = self.context["request"]
        tenant = request.tenant
        from inventory.models import Product
        product_ids = [it["product_id"] for it in data["items"]]
        products = Product.objects.filter(pk__in=product_ids, tenant=tenant).values_list('pk', flat=True)
        missing = set(product_ids) - set(products)
        if missing:
            raise serializers.ValidationError(f"Products not found or not in tenant: {missing}")
        return data

    def create(self, validated_data):
        # use service
        from .services import create_bill
        tenant = self.context["request"].tenant
        created_by_staff = getattr(self.context["request"].user, "staff_profile", None)
        bill = create_bill(tenant, created_by_staff, validated_data)
        return bill


class BillItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    class Meta:
        model = BillItem
        fields = ["bill_item_id", "product", "product_name", "quantity", "price", "discount", "subtotal"]


class BillDetailSerializer(serializers.ModelSerializer):
    items = BillItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    class Meta:
        model = Bill
        fields = ["bill_id", "date", "customer", "customer_name", "created_by", "item_total", "bill_discount", "gst_total", "grand_total", "payment_type", "items"]


class CustomerPaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerPayment
        fields = ["payment_id", "customer", "amount", "type", "date"]
        read_only_fields = ["payment_id", "date"]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Payment amount must be greater than zero.")
        return value

    def validate_customer(self, value):
        tenant = self.context["request"].tenant
        if value.tenant != tenant:
            raise serializers.ValidationError("Customer does not belong to your tenant.")
        return value

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return CustomerPayment.objects.create(tenant=tenant, **validated_data)
