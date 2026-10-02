import stripe
from django.core.management import call_command
from django.http import JsonResponse

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from Cart.models import Cart
from Products.models import Product
from Coupons.models import Coupon
from .models import Order, OrderItem, Payment, PaymentStatusLog
from .serializers import OrderSerializer


stripe.api_key = settings.STRIPE_SECRET_KEY


OPEN_STATUSES = [
    Order.Status.PENDING,
    Order.Status.FAILED
]


def find_order_and_payment(metadata):
    """
    Uses the ids we put in Stripe's metadata to find the exact Order and
    the exact Payment attempt an event belongs to. Since one Order now has
    many Payment rows (one per attempt), we can't just take .first().
    """

    order = Order.objects.filter(
        id=metadata.get('order_id')
    ).first()

    if not order:
        return None, None

    payment_id = metadata.get('payment_id')

    if payment_id:
        payment = Payment.objects.filter(
            id=payment_id,
            order=order
        ).first()
    else:
        payment = order.payments.order_by('-created_at').first()

    return order, payment


def release_order_stock(order):
    """Release stock reserved by an unpaid order."""
    for order_item in order.items.select_related('product'):
        if not order_item.product_id:
            continue

        product = Product.objects.select_for_update().get(
            pk=order_item.product_id
        )
        product.reserved_quantity -= order_item.quantity
        product.save(update_fields=['reserved_quantity'])


def finalize_order_stock(order):
    """Convert an order's reservation into a completed stock deduction."""
    for order_item in order.items.select_related('product'):
        if not order_item.product_id:
            continue

        product = Product.objects.select_for_update().get(
            pk=order_item.product_id
        )
        product.stock_quantity -= order_item.quantity
        product.reserved_quantity -= order_item.quantity
        product.save(update_fields=['stock_quantity', 'reserved_quantity'])


def create_payment_checkout_session(order):
    """
    Creates a new Payment attempt and Stripe Checkout Session
    for an existing Order.

    The Order's locked OrderItem prices are always used.
    """

    # ---------------------------------------------------------
    # 1. Expire Stripe sessions from earlier attempts of this
    #    order.
    # ---------------------------------------------------------
    old_payments = (
        order.payments
        .exclude(status=Payment.Status.SUCCEEDED)
        .exclude(stripe_session_id__isnull=True)
        .exclude(stripe_session_id='')
    )

    for old_payment in old_payments:
        try:
            stripe.checkout.Session.expire(
                old_payment.stripe_session_id
            )

            print(
                "Expired old Stripe session:",
                old_payment.stripe_session_id
            )

        except Exception as e:
            print(
                "Could not expire session",
                old_payment.stripe_session_id,
                "-",
                e
            )

    # ---------------------------------------------------------
    # 2. Record the new payment attempt FIRST.
    # ---------------------------------------------------------
    payment = Payment.objects.create(
        order=order,
        amount=order.total,
        status=Payment.Status.REQUIRES_PAYMENT
    )

    PaymentStatusLog.objects.create(
        payment=payment,
        status=Payment.Status.REQUIRES_PAYMENT
    )

    # ---------------------------------------------------------
    # 3. Create Stripe Checkout Session using the locked
    #    OrderItem prices.
    # ---------------------------------------------------------
    order_items = list(
        order.items.select_related('product')
    )

    metadata = {
        'order_id': str(order.id),
        'payment_id': str(payment.id),
    }

    session_kwargs = {
        'payment_method_types': ['card'],
        'metadata': metadata,
        'payment_intent_data': {
            'metadata': metadata
        },
        'line_items': [{
            'price_data': {
                'currency': 'usd',
                'product_data': {
                    'name': order_item.product.title
                },
                'unit_amount': int(
                    order_item.price_at_purchase * 100
                ),
            },
            'quantity': order_item.quantity,
        } for order_item in order_items],
        'mode': 'payment',
        'success_url': (
            f'{settings.SITE_URL}/checkout/success/'
        ),
        'cancel_url': (
            f'{settings.SITE_URL}/checkout/cancel/'
        ),
    }

    # ---------------------------------------------------------
    # 4. Coupon is taken from the EXISTING ORDER.
    # ---------------------------------------------------------
    if order.coupon:
        stripe_coupon = stripe.Coupon.create(
            percent_off=float(
                order.coupon.discount_percentage
            ) * 100,
            duration='once'
        )

        session_kwargs['discounts'] = [
            {'coupon': stripe_coupon.id}
        ]

    # ---------------------------------------------------------
    # 5. Create Stripe Checkout Session.
    # ---------------------------------------------------------
    try:
        session = stripe.checkout.Session.create(
            **session_kwargs
        )

    except Exception as e:
        print("Stripe session creation failed:", e)

        payment.status = Payment.Status.FAILED
        payment.save()

        PaymentStatusLog.objects.create(
            payment=payment,
            status=Payment.Status.FAILED
        )

        return None

    # ---------------------------------------------------------
    # 6. Save Stripe IDs.
    # ---------------------------------------------------------
    payment.stripe_session_id = session.id

    if session.payment_intent:
        payment.stripe_payment_intent_id = session.payment_intent

    payment.save()

    print(
        "Stripe session created:",
        session.id,
        "for Order",
        order.id,
        "Payment",
        payment.id
    )

    return session


class OrderListView(generics.ListAPIView):
    """GET /api/orders/ -> the logged-in user's own order history."""

    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).order_by('-created_at')


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_id):

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(
                    id=order_id,
                    user=request.user
                )

                if order.status not in OPEN_STATUSES:
                    return Response(
                        {
                            'detail': (
                                'Only pending or failed orders can be cancelled.'
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

                release_order_stock(order)

                order.status = Order.Status.CANCELLED
                order.save(update_fields=['status'])

        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                'detail': 'Order cancelled successfully.',
                'order_id': order.id
            },
            status=status.HTTP_200_OK
        )

class ExpireOrdersCronView(APIView):
    """
    GET /api/orders/expire/

    Called by Vercel Cron to automatically cancel
    pending/failed orders older than 24 hours.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):

        auth_header = request.headers.get('Authorization')

        expected_auth = f'Bearer {settings.CRON_SECRET}'

        if not settings.CRON_SECRET or auth_header != expected_auth:
            return Response(
                {'detail': 'Unauthorized.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        call_command('expire_orders')

        return Response(
            {'detail': 'Expired orders processed.'},
            status=status.HTTP_200_OK
        )


class CheckoutView(APIView):
    """
    POST /api/checkout/

    Always creates a NEW Order from the user's current cart.

    The cart is converted into OrderItems using the current product
    prices at the moment of checkout. Those prices are permanently
    stored in price_at_purchase.

    After the Order and OrderItems are created, the CartItems are
    removed because the cart has now become an Order.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):

        print("\n========== CHECKOUT VIEW HIT ==========")
        print("User:", request.user)

        cart = Cart.objects.filter(
            user=request.user
        ).first()

        if cart:
            cart.items.filter(
                product__owner=request.user
            ).delete()

        if not cart or not cart.items.exists():
            raise ValidationError(
                "Your cart is empty."
            )

        cart_items = list(
            cart.items.select_related('product')
        )

        try:
            with transaction.atomic():

                # -------------------------------------------------
                # 1. Lock products and reserve stock.
                # -------------------------------------------------
                locked_products = {}

                for item in sorted(cart_items, key=lambda x: x.product_id):
                    product = Product.objects.select_for_update().get(
                        pk=item.product_id
                    )
                    available_quantity = (
                        product.stock_quantity - product.reserved_quantity
                    )

                    if item.quantity > available_quantity:
                        raise ValidationError({
                            'stock': (
                                f'Not enough stock for "{product.title}". '
                                f'Available: {available_quantity}, '
                                f'requested: {item.quantity}.'
                            )
                        })

                    locked_products[item.product_id] = product

                subtotal = sum(
                    locked_products[item.product_id].price * item.quantity
                    for item in cart_items
                )

                # -------------------------------------------------
                # 2. Apply coupon to THIS NEW order.
                # -------------------------------------------------
                coupon = None
                discount_amount = 0

                coupon_code = request.data.get(
                    'coupon_code'
                )

                if coupon_code:
                    coupon = Coupon.objects.filter(
                        code=coupon_code.upper()
                    ).first()

                    if not coupon:
                        raise ValidationError({
                            'coupon_code': 'Invalid coupon code.'
                        })

                    if not coupon.is_valid():
                        raise ValidationError({
                            'coupon_code': 'This coupon has expired.'
                        })

                    discount_amount = (
                        subtotal *
                        coupon.discount_percentage
                    )

                total = subtotal - discount_amount

                # -------------------------------------------------
                # 3. ALWAYS create a NEW Order.
                # -------------------------------------------------
                order = Order.objects.create(
                    user=request.user,
                    coupon=coupon,
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    total=total,
                    status=Order.Status.PENDING
                )

                print(
                    "New Django Order created:",
                    order.id
                )
                
                # -------------------------------------------------
                # 4. Right after creating the order, clear any applied coupon in the session.
                # This ensures that the coupon is not reused in future checkouts.
                # -------------------------------------------------
                if 'applied_coupon' in request.session:
                     del request.session['applied_coupon']

                # -------------------------------------------------
                # 5. Copy CartItems -> OrderItems.
                # -------------------------------------------------
                for item in cart_items:
                    product = locked_products[item.product_id]

                    OrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=item.quantity,
                        price_at_purchase=product.price
                    )

                    product.reserved_quantity += item.quantity
                    product.save(update_fields=['reserved_quantity'])

                # -------------------------------------------------
                # 6. Empty cart immediately.
                # -------------------------------------------------
                cart.items.all().delete()

                print(
                    "Cart emptied after creating Order:",
                    order.id
                )

        except IntegrityError:
            return Response(
                {
                    'detail': (
                        'Could not create the order. '
                        'Please try again.'
                    )
                },
                status=status.HTTP_409_CONFLICT
            )

        # ---------------------------------------------------------
        # 7. Create first Payment + Stripe Session.
        # ---------------------------------------------------------
        session = create_payment_checkout_session(
            order
        )

        if session is None:
            return Response(
                {
                    'detail': (
                        'Order was created, but payment could not '
                        'be started. You can try Pay Order from '
                        'My Orders.'
                    ),
                    'order_id': order.id
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        print(
            "===========================================\n"
        )

        return Response(
            {
                'checkout_url': session.url,
                'order_id': order.id
            },
            status=status.HTTP_201_CREATED
        )


class PayOrderView(APIView):
    """
    POST /api/orders/<order_id>/pay/

    Starts a new Stripe payment attempt for an existing pending/failed
    order.

    The order's locked prices are used. The current Product.price is
    NOT used when creating the payment.

    Orders can only be paid within their original 24-hour payment window.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):

        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user
            )

        except Order.DoesNotExist:
            return Response(
                {'detail': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # ---------------------------------------------------------
        # Only pending or failed orders can be paid.
        # ---------------------------------------------------------
        if order.status not in OPEN_STATUSES:
            return Response(
                {
                    'detail': (
                        'Only pending or failed orders can be paid.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------
        # Check 24-hour payment window.
        # ---------------------------------------------------------
        if timezone.now() >= order.payment_deadline:

            with transaction.atomic():
                order = Order.objects.select_for_update().get(
                    id=order_id,
                    user=request.user
                )

                if order.status in OPEN_STATUSES:
                    release_order_stock(order)
                    order.status = Order.Status.CANCELLED
                    order.save(update_fields=['status'])

            return Response(
                {
                    'detail': (
                        'This order has expired because the '
                        '24-hour payment window has ended.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # ---------------------------------------------------------
        # Keep order pending while a new payment attempt starts.
        # ---------------------------------------------------------
        order.status = Order.Status.PENDING

        order.save(
            update_fields=['status']
        )

        # ---------------------------------------------------------
        # Create a NEW payment attempt and NEW Stripe session.
        # ---------------------------------------------------------
        session = create_payment_checkout_session(
            order
        )

        if session is None:
            return Response(
                {
                    'detail': (
                        'Could not start the payment. '
                        'Please try again.'
                    )
                },
                status=status.HTTP_502_BAD_GATEWAY
            )

        return Response(
            {
                'checkout_url': session.url,
                'order_id': order.id
            },
            status=status.HTTP_200_OK
        )


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    POST /api/webhook/stripe/

    Receives Stripe webhook events and updates the matching Order and
    the exact Payment attempt, logging every transition.
    """

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):

        payload = request.body
        sig_header = request.META.get(
            'HTTP_STRIPE_SIGNATURE'
        )

        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                settings.STRIPE_WEBHOOK_SECRET
            )

        except ValueError as e:
            print(
                "Webhook payload error:",
                e
            )

            return Response(
                {'detail': 'Invalid payload.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        except stripe.error.SignatureVerificationError as e:
            print(
                "Webhook signature error:",
                e
            )

            return Response(
                {'detail': 'Invalid signature.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        print(
            "Stripe event received:",
            event['type']
        )

        if event['type'] == 'checkout.session.completed':

            session = event['data']['object']

            print(
                "Stripe session ID:",
                session.id
            )

            print(
                "Payment Intent:",
                session.payment_intent
            )

            print(
                "Metadata:",
                session.metadata
            )

            metadata = session.metadata.to_dict()

            if not metadata.get('order_id'):
                print(
                    "No order_id found in Stripe metadata. "
                    "Ignoring this event."
                )

                return Response(
                    {
                        'detail': (
                            'No order_id in metadata.'
                        )
                    },
                    status=status.HTTP_200_OK
                )

            order, payment = find_order_and_payment(
                metadata
            )

            print(
                "Order found:",
                order
            )

            print(
                "Payment found:",
                payment
            )

            if not order:
                return Response(
                    {'detail': 'Order not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not payment:
                return Response(
                    {'detail': 'Payment not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Stripe can deliver the same event more than once.
            if payment.status == Payment.Status.SUCCEEDED:

                print(
                    f"Payment #{payment.id} already processed. "
                    "Ignoring duplicate."
                )

                return Response(
                    {'detail': 'Already processed.'},
                    status=status.HTTP_200_OK
                )

            # -----------------------------------------------------
            # Do not allow a payment to complete an already
            # cancelled order.
            # -----------------------------------------------------
            if order.status == Order.Status.CANCELLED:

                print(
                    f"Order #{order.id} is already cancelled. "
                    f"Ignoring successful payment #{payment.id}."
                )

                return Response(
                    {
                        'detail': (
                            'Order already cancelled.'
                        )
                    },
                    status=status.HTTP_200_OK
                )

            # If another payment attempt already paid this order, do not
            # deduct stock a second time.
            if order.status == Order.Status.PAID:
                print(
                    f"Order #{order.id} is already paid. "
                    f"Ignoring successful payment #{payment.id}."
                )
                return Response(
                    {'detail': 'Order already paid.'},
                    status=status.HTTP_200_OK
                )

            with transaction.atomic():
                order = Order.objects.select_for_update().get(
                    id=order.id
                )
                payment = Payment.objects.select_for_update().get(
                    id=payment.id,
                    order=order
                )

                if payment.status == Payment.Status.SUCCEEDED or order.status == Order.Status.PAID:
                    return Response(
                        {'detail': 'Already processed.'},
                        status=status.HTTP_200_OK
                    )

                if order.status == Order.Status.CANCELLED:
                    return Response(
                        {'detail': 'Order already cancelled.'},
                        status=status.HTTP_200_OK
                    )

                # Update Payment.
                payment.stripe_payment_intent_id = (
                    session.payment_intent
                )

                payment.status = Payment.Status.SUCCEEDED
                payment.save()

                PaymentStatusLog.objects.create(
                    payment=payment,
                    status=Payment.Status.SUCCEEDED
                )

                # Convert the stock reservation into a completed sale.
                finalize_order_stock(order)

                # Update Order.
                order.status = Order.Status.PAID
                order.save()

            print(
                f"Order #{order.id} marked as PAID "
                f"(attempt #{payment.id})."
            )

        elif event['type'] == 'payment_intent.payment_failed':

            payment_intent = event['data']['object']

            print(
                "Stripe PaymentIntent ID:",
                payment_intent.id
            )

            print(
                "Metadata:",
                payment_intent.metadata
            )

            metadata = payment_intent.metadata.to_dict()

            if not metadata.get('order_id'):

                print(
                    "No order_id found in Stripe metadata. "
                    "Ignoring this event."
                )

                return Response(
                    {
                        'detail': (
                            'No order_id in metadata.'
                        )
                    },
                    status=status.HTTP_200_OK
                )

            order, payment = find_order_and_payment(
                metadata
            )

            print(
                "Order found:",
                order
            )

            print(
                "Payment found:",
                payment
            )

            if not order:
                return Response(
                    {'detail': 'Order not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            if not payment:
                return Response(
                    {'detail': 'Payment not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # A late/out-of-order failure event must never
            # undo a success.
            if payment.status == Payment.Status.SUCCEEDED:

                print(
                    f"Payment #{payment.id} already succeeded. "
                    "Ignoring failure event."
                )

                return Response(
                    {'detail': 'Already succeeded.'},
                    status=status.HTTP_200_OK
                )

            payment.stripe_payment_intent_id = (
                payment.stripe_payment_intent_id
                or payment_intent.id
            )

            payment.status = Payment.Status.FAILED

            payment.save()

            PaymentStatusLog.objects.create(
                payment=payment,
                status=Payment.Status.FAILED
            )

            if order.status != Order.Status.PAID:
                order.status = Order.Status.FAILED

                order.save()

            print(
                f"Order #{order.id} marked as FAILED "
                f"(attempt #{payment.id})."
            )

        return Response(
            {'detail': 'Webhook received.'},
            status=status.HTTP_200_OK
        )