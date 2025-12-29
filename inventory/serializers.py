from rest_framework import serializers
from .models import Category, Product, ProductImage, StockMovement

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            "category_id",
            "name",
            "description",
            "status",
            "created_at"
        ]
        read_only_fields = ["category_id", "created_at"]

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "product_id",
            "name",
            "sku",
            "brand",
            "size",
            "description",
            "unit",
            "category",
            "purchase_price",
            "selling_price",
            "mrp",
            "current_stock",
            "low_stock_alert",
            "hsn_code",
            "gst_percent",
            "status",
            "created_at"
        ]

        read_only_fields = [
            "product_id",
            "created_at",
            "current_stock",  # stock should be updated via StockMovement only
        ]

    def validate(self, data):
        request = self.context.get("request")
        tenant = request.tenant

        #validation: category must belong to same tenant
        if "category" in data:
            if data["category"].tenant != tenant:
                raise serializers.ValidationError("Category must belong to your tenant")

        return data

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["image_id", "product", "image", "uploaded_at"] 
        read_only_fields = ["image_id", "uploaded_at"]

class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            "movement_id",
            "type",
            "quantity",
            "reference_type",
            "reason",
            "date",
            "product_name",
        ]
        read_only_fields = fields