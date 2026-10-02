import uuid
from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex


class Product(models.Model):
    """
    A product listed by a user. Each product has a unique, auto-generated
    serial number and belongs to exactly one owner (the user who created it).
    """

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    serial_number = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def available_quantity(self):
        return max(self.stock_quantity - self.reserved_quantity,0)

    class Meta:
        indexes = [
            GinIndex(fields=['title'], name='product_title_trgm_idx', opclasses=['gin_trgm_ops']),
            GinIndex(fields=['description'], name='product_desc_trgm_idx', opclasses=['gin_trgm_ops']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate a unique serial number on first save only.
        if not self.serial_number:
            self.serial_number = self.generate_unique_serial_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_serial_number():
        """
        Generates a short, unique, human-readable serial number, e.g. 'PRD-3F9A2B1C'.
        Loops (extremely rarely more than once) to guarantee no collision
        even under concurrent product creation.
        """
        while True:
            candidate = f"PRD-{uuid.uuid4().hex[:8].upper()}"
            if not Product.objects.filter(serial_number=candidate).exists():
                return candidate

    def __str__(self):
        return f"{self.title} ({self.serial_number})"


class ProductImage(models.Model):
    """
    A single image belonging to a product. A product can have many of these
    (one-to-many), satisfying the 'many images' requirement.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='product_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"