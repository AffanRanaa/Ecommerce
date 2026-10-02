from django.urls import path
from .template_views import checkout_success_page, checkout_cancel_page, order_history_page

urlpatterns = [
    path('checkout/success/', checkout_success_page, name='checkout-success-page'),
    path('checkout/cancel/', checkout_cancel_page, name='checkout-cancel-page'),
    path('orders/', order_history_page, name='order-history-page'),
]