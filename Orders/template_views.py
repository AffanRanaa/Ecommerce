from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Order


@login_required
def checkout_success_page(request):
    return render(request, 'Orders/success.html')


@login_required
def checkout_cancel_page(request):
    return render(request, 'Orders/cancel.html')


@login_required
def order_history_page(request):
    """
    Shows the logged-in user's own orders — status, items, and payment
    attempts. Uses the ORM directly (not the DRF API) since this page is
    just a one-time load with no live-update interaction, same reasoning
    as the product list/detail pages.
    """
    orders = (
        Order.objects.filter(user=request.user)
        .prefetch_related('items__product', 'payments__status_logs')
        .select_related('coupon')
        .order_by('-created_at')
    )
    return render(request, 'Orders/history.html', {'orders': orders})