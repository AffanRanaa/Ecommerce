from django.contrib import admin
from .models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """
    Lets you add/remove multiple ProductImage rows directly inside the
    Product admin page, instead of a separate, disconnected section.
    extra=3 shows 3 empty image-upload slots by default — add more
    manually if needed, they don't overwrite each other.
    """
    model = ProductImage
    extra = 3


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'serial_number', 'owner', 'price', 'stock_quantity','reserved_quantity','available_quantity',]
    search_fields = ['title', 'serial_number']
    inlines = [ProductImageInline]
    @admin.display(description='Available Quantity')
    def available_quantity(self, obj):
        return max(obj.stock_quantity - obj.reserved_quantity, 0)

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'uploaded_at']
    
