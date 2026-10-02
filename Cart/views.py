from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404

from Products.models import Product
from Coupons.models import Coupon
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
from .session_cart import SessionCart


def calculate_cart_totals(request):
    subtotal = 0

    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()

        if cart:
            cart.items.filter(product__owner=request.user).delete()

            items = cart.items.select_related('product').all()

            for item in items:
                subtotal += item.product.price * item.quantity

    else:
        session_cart = SessionCart(request)
        product_ids = session_cart.items().keys()
        products = Product.objects.filter(id__in=product_ids)

        for product in products:
            quantity = session_cart.items()[str(product.id)]
            subtotal += product.price * quantity

    discount_amount = 0
    coupon = None

    applied_coupon_code = request.session.get('applied_coupon')

    if applied_coupon_code:
        coupon = Coupon.objects.filter(
            code=applied_coupon_code
        ).first()

        if coupon and coupon.is_valid():
            discount_amount = subtotal * coupon.discount_percentage
        else:
            del request.session['applied_coupon']
            coupon = None

    total = subtotal - discount_amount

    return subtotal, coupon, discount_amount, total


class CartViewSet(viewsets.ViewSet):

    permission_classes = [AllowAny]

    def list(self, request):
        if request.user.is_authenticated:
            cart = Cart.objects.filter(
                user=request.user
            ).first()

            if not cart:
                return Response({
                    'id': None,
                    'items': [],
                    'created_at': None,
                    'updated_at': None
                })

            serializer = CartSerializer(cart)

            return Response(serializer.data)

        return Response({
            'id': None,
            'items': [],
            'created_at': None,
            'updated_at': None
        })

    @action(
        detail=False,
        methods=['post'],
        url_path=r'update/(?P<item_id>\d+)'
    )
    def update_item(self, request, item_id):

        quantity = int(
            request.data.get('quantity', 1)
        )

        if request.user.is_authenticated:

            item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user
            )

            item.quantity = quantity
            item.save()

            line_total = (
                item.product.price * item.quantity
            )

            item_serializer = CartItemSerializer(item)

        else:

            session_cart = SessionCart(request)
            session_items = session_cart.items()

            if str(item_id) not in session_items:
                return Response(
                    {'error': 'Cart item not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            session_cart.update_quantity(
                item_id,
                quantity
            )

            product = get_object_or_404(
                Product,
                id=item_id
            )

            line_total = product.price * quantity

            item_serializer = None

        subtotal, coupon, discount_amount, total = (
            calculate_cart_totals(request)
        )

        response_data = {
            'line_total': line_total,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total': total
        }

        if item_serializer:
            response_data['item'] = item_serializer.data

        return Response(
            response_data,
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['post'],
        url_path=r'remove/(?P<item_id>\d+)'
    )
    def remove_item(self, request, item_id):

        if request.user.is_authenticated:

            item = get_object_or_404(
                CartItem,
                id=item_id,
                cart__user=request.user
            )

            item.delete()

        else:

            session_cart = SessionCart(request)

            if str(item_id) not in session_cart.items():
                return Response(
                    {'error': 'Cart item not found.'},
                    status=status.HTTP_404_NOT_FOUND
                )

            session_cart.remove(item_id)

        subtotal, coupon, discount_amount, total = (
            calculate_cart_totals(request)
        )

        if request.user.is_authenticated:

            cart = Cart.objects.filter(
                user=request.user
            ).first()

            cart_empty = (
                not cart or not cart.items.exists()
            )

        else:

            session_cart = SessionCart(request)
            cart_empty = not session_cart.items()

        return Response({
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total': total,
            'cart_empty': cart_empty
        }, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='apply-coupon'
    )
    def apply_coupon(self, request):

        code = request.data.get(
            'coupon_code',
            ''
        ).strip().upper()

        coupon = Coupon.objects.filter(
            code=code
        ).first()

        if not coupon:
            return Response(
                {'error': 'Invalid coupon code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not coupon.is_valid():
            return Response(
                {'error': 'This coupon has expired.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.session['applied_coupon'] = coupon.code

        subtotal, coupon, discount_amount, total = (
            calculate_cart_totals(request)
        )

        coupon_percent = int(
            coupon.discount_percentage * 100
        )

        return Response({
            'coupon_code': coupon.code,
            'coupon_percent': coupon_percent,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'total': total
        }, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['post'],
        url_path='remove-coupon'
    )
    def remove_coupon(self, request):

        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']

        subtotal, coupon, discount_amount, total = (
            calculate_cart_totals(request)
        )

        return Response({
            'subtotal': subtotal,
            'discount_amount': 0,
            'total': total
        }, status=status.HTTP_200_OK)