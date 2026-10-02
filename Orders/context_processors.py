from .models import Order


def pending_order_count(request):
    if not request.user.is_authenticated:
        return {'pending_order_count': 0}

    count = Order.objects.filter(
        user=request.user,
         status__in=[Order.Status.PENDING, Order.Status.FAILED]
    ).count()

    return {'pending_order_count': count}