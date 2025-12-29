from django.contrib import admin
from .models import Category, Product, ProductImage, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['category_id', 'name', 'tenant', 'status', 'created_at']
    list_filter = ['status', 'tenant', 'created_at']
    search_fields = ['name', 'description', 'tenant__business_name']
    readonly_fields = ['category_id', 'created_at', 'updated_at']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'status')
        }),
        ('Tenant', {
            'fields': ('tenant',)
        }),
        ('Metadata', {
            'fields': ('category_id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'name', 'sku', 'tenant', 'category', 'selling_price', 'current_stock', 'status']
    list_filter = ['status', 'tenant', 'category', 'created_at']
    search_fields = ['name', 'sku', 'brand', 'tenant__business_name', 'category__name']
    readonly_fields = ['product_id', 'created_at', 'current_stock']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'brand', 'status')
        }),
        ('Relationships', {
            'fields': ('tenant', 'category')
        }),
        ('Pricing', {
            'fields': ('purchase_price', 'selling_price', 'mrp')
        }),
        ('Stock', {
            'fields': ('current_stock', 'low_stock_alert')
        }),
        ('Tax Information', {
            'fields': ('hsn_code', 'gst_percent')
        }),
        ('Metadata', {
            'fields': ('product_id', 'created_at'),
            'classes': ('collapse',)
        }),
    )


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['image_id', 'uploaded_at']
    fields = ['image', 'uploaded_at']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['image_id', 'product', 'uploaded_at']
    list_filter = ['uploaded_at', 'product__tenant']
    search_fields = ['product__name', 'product__sku']
    readonly_fields = ['image_id', 'uploaded_at']
    ordering = ['-uploaded_at']


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['movement_id', 'product', 'type', 'quantity', 'tenant', 'reference_type', 'date']
    list_filter = ['type', 'tenant', 'date', 'reference_type']
    search_fields = ['product__name', 'product__sku', 'reason', 'reference_type']
    readonly_fields = ['movement_id', 'date']
    ordering = ['-date']
    
    fieldsets = (
        ('Movement Information', {
            'fields': ('type', 'quantity', 'reference_type', 'reason')
        }),
        ('Relationships', {
            'fields': ('tenant', 'product')
        }),
        ('Metadata', {
            'fields': ('movement_id', 'date'),
            'classes': ('collapse',)
        }),
    )


# Optional: Add ProductImage inline to ProductAdmin
ProductAdmin.inlines = [ProductImageInline]
