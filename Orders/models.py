from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from Products.models import Product
from Coupons.models import Coupon
from datetime import timedelta


class Order(models.Model):
    """
    Represents one checkout attempt/purchase by a user. Created at the
    start of checkout, then its status is updated as the Stripe payment
    progresses. This is the core record satisfying the requirement to
    'maintain all kinds of data around user actions of orders/payments'.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        CANCELLED = 'cancelled', 'Cancelled'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def payment_deadline(self):
        return self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Order #{self.id} by {self.user.username} ({self.status})"


class OrderItem(models.Model):
    """
    A single product line within an order. Stores price_at_purchase
    separately from the live Product.price, so historical orders stay
    accurate even if the product's price changes later.
    """

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity} x {self.product} (Order #{self.order_id})"


class Payment(models.Model):
    """
    Records a single Stripe payment attempt tied to an order. Kept separate
    from Order so that retries (e.g. a failed attempt followed by a
    successful one) are each logged individually, not overwritten.
    """

    class Status(models.TextChoices):
        REQUIRES_PAYMENT = 'requires_payment', 'Requires Payment'
        SUCCEEDED = 'succeeded', 'Succeeded'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    stripe_session_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.REQUIRES_PAYMENT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for Order #{self.order_id} - {self.status}"


class PaymentStatusLog(models.Model):
    """
    Records EVERY status change a Payment goes through over time, even
    when Stripe reuses the same PaymentIntent across retries within one
    Checkout Session (which would otherwise silently overwrite the single
    Payment row's status — losing the "first failed, then succeeded"
    history the project requires). Payment.status always reflects the
    CURRENT/latest state; this table is the full timeline underneath it.
    """

    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='status_logs'
    )
    status = models.CharField(max_length=20, choices=Payment.Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']  # chronological order — oldest attempt first

    def __str__(self):
        return f"Payment #{self.payment_id} -> {self.status} at {self.created_at}"