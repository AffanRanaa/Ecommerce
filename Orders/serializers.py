from rest_framework import serializers
from .models import Order, OrderItem, Payment


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.ReadOnlyField(source='product.title')

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_title', 'quantity', 'price_at_purchase']


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'stripe_payment_intent_id', 'amount', 'status', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """
    Read-only view of an order — used for order history / confirmation
    pages, not for creating orders (that's a separate checkout flow with
    its own logic, not a plain serializer .create()).
    """
    items = OrderItemSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    coupon_code = serializers.ReadOnlyField(source='coupon.code')

    class Meta:
        model = Order
        fields = [
            'id', 'status', 'coupon_code', 'subtotal', 'discount_amount',
            'total', 'items', 'payments', 'created_at'
        ]