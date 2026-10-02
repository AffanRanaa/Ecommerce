from django.urls import path
from .template_views import (
    add_to_cart_view, cart_page_view
)

urlpatterns = [
    path('cart/', cart_page_view, name='cart-page'),
    path('cart/add/<int:product_id>/', add_to_cart_view, name='add-to-cart'),
]