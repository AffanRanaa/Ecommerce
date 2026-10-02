from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone


class Coupon(models.Model):
    """
    A promo code, created only via Django admin (no user-facing UI needed
    per requirements). Applied during checkout to give a percentage
    discount, as long as it hasn't passed its valid_til date.
    """

    code_validator = RegexValidator(
        regex=r'^[A-Z0-9]{4,10}$',
        message='Code must be 4-10 characters, uppercase letters and/or digits only.'
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        validators=[code_validator]
    )
    discount_percentage = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(0.01), MaxValueValidator(1.00)],
        help_text='Stored as a fraction, e.g. 0.30 means 30% off.'
    )
    valid_til = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Enforce uppercase even if someone types lowercase in the admin form.
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def is_valid(self):
        """Returns True if this coupon can still be used right now."""
        return timezone.now() <= self.valid_til

    def __str__(self):
        return f"{self.code} ({self.discount_percentage * 100}% off)"