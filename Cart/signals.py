from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from Products.models import Product
from .models import Cart, CartItem
from .session_cart import SessionCart


@receiver(user_logged_in)
def merge_session_cart_on_login(sender, request, user, **kwargs):
    """
    Fires automatically every time ANY user logs in (signup's auto-login
    counts too, since it also calls Django's login()). Moves whatever was
    in their guest session cart into their real database cart, then
    empties the session cart so it isn't merged again on next login.
    """
    session_cart = SessionCart(request)
    guest_items = session_cart.items()

    if not guest_items:
        return  # nothing to merge

    cart, _ = Cart.objects.get_or_create(user=user)

    for product_id, quantity in guest_items.items():
        product = Product.objects.filter(id=product_id).first()
        if product is None:
            continue  # product may have been deleted since it was added

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={'quantity': quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()

    session_cart.clear()