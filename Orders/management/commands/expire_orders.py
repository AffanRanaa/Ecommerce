from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from Orders.models import Order
from Orders.views import release_order_stock


class Command(BaseCommand):
    help = 'Automatically cancels unpaid orders older than 24 hours.'

    def handle(self, *args, **options):

        expiry_time = timezone.now() - timedelta(hours=24)

        expired_orders = Order.objects.filter(
            status__in=[
                Order.Status.PENDING,
                Order.Status.FAILED
            ],
            created_at__lte=expiry_time
        )

        count = 0

        for order_id in expired_orders.values_list('id', flat=True):
            with transaction.atomic():
                order = (
                    Order.objects
                    .select_for_update()
                    .filter(
                        id=order_id,
                        status__in=[
                            Order.Status.PENDING,
                            Order.Status.FAILED
                        ],
                        created_at__lte=expiry_time
                    )
                    .first()
                )

                if not order:
                    continue

                release_order_stock(order)

                order.status = Order.Status.CANCELLED
                order.save(update_fields=['status'])

                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{count} expired order(s) cancelled.'
            )
        )
