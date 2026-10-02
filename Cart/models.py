from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from Products.models import Product


class Cart(models.Model):
    """
    One cart per logged-in user. Guest (not-logged-in) carts are handled
    separately using Django sessions in the view layer — they don't get a
    row here until the guest signs up/logs in and their session cart is
    merged into a real Cart.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class CartItem(models.Model):
    """
    A single product line inside a cart, with its quantity. A cart can
    have many items (one-to-many). Ownership restriction ('can't add own
    product') is enforced at the serializer/view level, not here.
    """

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevents the same product appearing as two separate rows in one
        # cart — adding an already-present product again should update its
        # quantity instead, handled in the view/serializer logic.
        unique_together = ('cart', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.title} in {self.cart.user.username}'s cart"