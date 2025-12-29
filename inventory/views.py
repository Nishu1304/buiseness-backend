from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.http import HttpResponse
import csv
import io

from core.mixins import TenantViewSetMixin
from core.permissions import IsTenantUser

from .models import Category, Product, ProductImage, StockMovement
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductImageSerializer,
    StockMovementSerializer
)

class CategoryViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantUser]
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

class ProductViewSet(TenantViewSetMixin, viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "sku", "brand"]
    ordering_fields = ["selling_price", "current_stock"]
    filterset_fields = ["category", "status"]

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)

    @action(detail=True, methods=["GET"], url_path="stock-history")
    def stock_history(self, request, pk=None):
        product = self.get_object()
        movements = product.movements.order_by("-date")
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["POST"], url_path="add-stock")
    def add_stock(self, request, pk=None):
        product = self.get_object()
        quantity = int(request.data.get("quantity", 0))

        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than 0"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update product stock
        product.current_stock += quantity
        product.save()

        # Create stock movement
        StockMovement.objects.create(
            tenant=self.request.tenant,
            product=product,
            type="IN",
            quantity=quantity,
            reference_type="Manual Stock Add",
            reason=request.data.get("reason", ""),
        )

        return Response(
            {"message": "Stock added successfully", "new_stock": product.current_stock},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["POST"], url_path="remove-stock")
    def remove_stock(self, request, pk=None):
        product = self.get_object()
        quantity = int(request.data.get("quantity", 0))

        if quantity <= 0:
            return Response(
                {"error": "Quantity must be greater than zero."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        if product.current_stock < quantity:
            return Response(
                {"error": "Insufficient stock."}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update stock
        product.current_stock -= quantity
        product.save()

        # Log stock movement
        StockMovement.objects.create(
            tenant=self.request.tenant,
            product=product,
            type="OUT",
            quantity=quantity,
            reference_type="Manual Stock Deduction",
            reason=request.data.get("reason", "")
        )

        return Response(
            {"message": "Stock reduced successfully.", "new_stock": product.current_stock},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["GET"], url_path="images")
    def images(self, request, pk=None):
        """Get all images for a specific product"""
        product = self.get_object()
        images = ProductImage.objects.filter(product=product)
        serializer = ProductImageSerializer(images, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=["GET"], url_path="export-csv")
    def export_csv(self, request):
        """Export all products as CSV file"""
        products = self.get_queryset()
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
        
        writer = csv.writer(response)
        # Header row
        writer.writerow([
            'name', 'sku', 'category', 'brand', 'size', 'description', 'unit',
            'purchase_price', 'selling_price', 'mrp', 'current_stock', 
            'low_stock_alert', 'hsn_code', 'gst_percent', 'status'
        ])
        
        for product in products:
            writer.writerow([
                product.name,
                product.sku,
                product.category.name if product.category else '',
                product.brand or '',
                product.size or '',
                product.description or '',
                product.unit,
                str(product.purchase_price),
                str(product.selling_price),
                str(product.mrp) if product.mrp else '',
                product.current_stock,
                product.low_stock_alert,
                product.hsn_code or '',
                str(product.gst_percent),
                product.status
            ])
        
        return response

    @action(detail=False, methods=["POST"], url_path="import-csv")
    def import_csv(self, request):
        """Import products from a CSV file"""
        csv_file = request.FILES.get('file')
        
        if not csv_file:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not csv_file.name.endswith('.csv'):
            return Response(
                {"error": "File must be a CSV"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Read and decode the file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                try:
                    # Get or create category
                    category_name = row.get('category', '').strip()
                    if not category_name:
                        errors.append(f"Row {row_num}: Category is required")
                        error_count += 1
                        continue
                    
                    category, _ = Category.objects.get_or_create(
                        tenant=request.tenant,
                        name=category_name,
                        defaults={'status': 'active'}
                    )
                    
                    # Check if product with same SKU exists
                    sku = row.get('sku', '').strip()
                    if not sku:
                        # Generate a random SKU if not provided
                        import random
                        sku = str(random.randint(10000, 99999))
                    
                    existing_product = Product.objects.filter(
                        tenant=request.tenant, 
                        sku=sku
                    ).first()
                    
                    product_data = {
                        'name': row.get('name', '').strip(),
                        'sku': sku,
                        'category': category,
                        'brand': row.get('brand', '').strip() or None,
                        'size': row.get('size', '').strip() or None,
                        'description': row.get('description', '').strip() or None,
                        'unit': row.get('unit', 'pcs').strip(),
                        'purchase_price': float(row.get('purchase_price', 0) or 0),
                        'selling_price': float(row.get('selling_price', 0) or 0),
                        'mrp': float(row.get('mrp', 0) or 0) if row.get('mrp') else None,
                        'current_stock': int(row.get('current_stock', 0) or 0),
                        'low_stock_alert': int(row.get('low_stock_alert', 0) or 0),
                        'hsn_code': row.get('hsn_code', '').strip() or None,
                        'gst_percent': float(row.get('gst_percent', 0) or 0),
                        'status': row.get('status', 'active').strip(),
                    }
                    
                    if not product_data['name']:
                        errors.append(f"Row {row_num}: Product name is required")
                        error_count += 1
                        continue
                    
                    if existing_product:
                        # Update existing product
                        for key, value in product_data.items():
                            setattr(existing_product, key, value)
                        existing_product.save()
                    else:
                        # Create new product
                        product_data['tenant'] = request.tenant
                        Product.objects.create(**product_data)
                    
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
            
            return Response({
                "message": f"Import completed. {success_count} products imported successfully.",
                "success_count": success_count,
                "error_count": error_count,
                "errors": errors[:10]  # Limit errors to first 10
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to process CSV: {str(e)}"}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantUser]

    def get_queryset(self):
        return ProductImage.objects.filter(product__tenant=self.request.tenant)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["product", "type"]
    ordering_fields = ["date"]
    ordering = ["-date"]

    def get_queryset(self):
        return StockMovement.objects.filter(product__tenant=self.request.tenant)
