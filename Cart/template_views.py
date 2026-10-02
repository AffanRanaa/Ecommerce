from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from Products.models import Product
from Coupons.models import Coupon
from .models import Cart, CartItem
from .session_cart import SessionCart


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.owner == request.user:
        messages.error(request, "You cannot add your own product to your cart.")
        return redirect('product-detail-page', pk=product_id)

    quantity = int(request.POST.get('quantity', 1))

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect('product-detail-page', pk=product_id)

    # Available stock = total stock - stock already reserved
    available_quantity = (product.stock_quantity - product.reserved_quantity )

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)

        existing_item = CartItem.objects.filter( cart=cart,product=product).first()

        # If the product is already in the cart, the requested quantity
        # will be added to the existing quantity.
        current_cart_quantity = (existing_item.quantity if existing_item else 0)
        requested_total = current_cart_quantity + quantity

        if requested_total > available_quantity:
            messages.error(
                request,
                f'Not enough stock for "{product.title}". '
                f'Available: {available_quantity}, '
                f'you already have {current_cart_quantity} in your cart '
                f'and requested {quantity} more.'
            )
            return redirect('product-detail-page',pk=product_id )

        if existing_item:
            existing_item.quantity = requested_total
            existing_item.save(update_fields=['quantity'])
        else:
            CartItem.objects.create( cart=cart, product=product, quantity=quantity )

    else:
        # Guest — goes into the session instead of the database.
        session_cart = SessionCart(request)

        current_cart_quantity = session_cart.items().get( str(product_id), 0 )
        requested_total = current_cart_quantity + quantity

        if requested_total > available_quantity:
            messages.error(
                request,
                f'Not enough stock for "{product.title}". '
                f'Available: {available_quantity}, '
                f'you already have {current_cart_quantity} in your cart '
                f'and requested {quantity} more.'
            )
            return redirect( 'product-detail-page', pk=product_id )

        session_cart.add(product_id, quantity)

    messages.success(request,f"{product.title} added to cart.")

    return redirect('product-detail-page',pk=product_id )


def cart_page_view(request):
    """
    Builds a unified list of (product, quantity, item_id) regardless of
    whether the cart lives in the database or the session, so the same
    template works for both guest and logged-in users. Also applies
    whatever coupon code is stored in the session (if any) to compute
    discount_amount and total — the SAME calculation CheckoutView will
    redo later, this is just for display before the user commits to paying.
    """
    cart_rows = []
    subtotal = 0

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        removed_count, _ = cart.items.filter(product__owner=request.user).delete()
        if removed_count:
            messages.warning(request, "You cannot add your own products in the cart.")
        for item in cart.items.select_related('product').all():
            line_total = item.product.price * item.quantity
            subtotal += line_total
            cart_rows.append({'item_id': item.id, 'product': item.product, 'quantity': item.quantity, 'line_total': line_total})
    else:
        session_cart = SessionCart(request)
        product_ids = session_cart.items().keys()
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            quantity = session_cart.items()[str(product.id)]
            line_total = product.price * quantity
            subtotal += line_total
            cart_rows.append({'item_id': product.id, 'product': product, 'quantity': quantity, 'line_total': line_total})

    # --- apply session-stored coupon, if any, for display purposes ---
    applied_coupon_code = request.session.get('applied_coupon')
    discount_amount = 0
    coupon = None

    if applied_coupon_code:
        coupon = Coupon.objects.filter(code=applied_coupon_code).first()
        if coupon and coupon.is_valid():
            discount_amount = subtotal * coupon.discount_percentage
        else:
            # coupon expired or got deleted since it was applied — clear it
            del request.session['applied_coupon']
            coupon = None

    total = subtotal - discount_amount

    # convert 0.50 -> 50 here, once, so the template just displays a
    # number instead of doing (and getting wrong) the math itself
    coupon_percent = int(coupon.discount_percentage * 100) if coupon else 0

    return render(request, 'Cart/cart.html', {
        'cart_rows': cart_rows,
        'subtotal': subtotal,
        'coupon': coupon,
        'coupon_percent': coupon_percent,
        'discount_amount': discount_amount,
        'total': total,
    })


