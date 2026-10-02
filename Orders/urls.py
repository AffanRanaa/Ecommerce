from django.urls import path
from .views import OrderListView, CheckoutView, StripeWebhookView, CancelOrderView, PayOrderView

urlpatterns = [
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('webhook/stripe/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('orders/<int:order_id>/cancel/', CancelOrderView.as_view(), name='cancel-order'),
    path('orders/<int:order_id>/pay/',PayOrderView.as_view(),name='pay-order'
),
]