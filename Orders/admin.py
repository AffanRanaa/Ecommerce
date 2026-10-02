from django.contrib import admin
from .models import Order, OrderItem, Payment, PaymentStatusLog


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


class PaymentStatusLogInline(admin.TabularInline):
    """Shows the full attempt history right on the Payment's admin page —
    e.g. requires_payment -> failed -> succeeded, each with its own timestamp."""
    model = PaymentStatusLog
    extra = 0
    readonly_fields = ['status', 'created_at']
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'subtotal', 'discount_amount', 'total', 'created_at']
    list_filter = ['status']
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'status', 'amount', 'created_at']
    list_filter = ['status']
    inlines = [PaymentStatusLogInline]