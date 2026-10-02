from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .models import Product


def product_list_page(request):
    products = Product.objects.all().order_by('-created_at')

    # basic search via ?q= — a real GET form submit, page reload each time.
    # Phase 8/9 will replace this with a live, no-reload search using DRF.
    query = request.GET.get('q')
    if query:
        products = products.filter(title__icontains=query)

    return render(request, 'products/list.html', {'products': products, 'query': query})


def product_detail_page(request, pk):
    # product.comments.all() and product.images.all() are available in the
    # template directly via the related_name we set on those models —
    # no API call needed to render the initial page.
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/detail.html', {'product': product})


@login_required
def product_add_page(request):
    """Just renders the empty form — actual product creation happens via
    the DRF API (POST /api/products/), called by this page's own JS."""
    return render(request, 'Products/add.html')


@login_required
def product_edit_page(request, pk):
    """
    Renders the edit form pre-filled with the product's current data.
    Ownership check happens here at the page level (not just relying on
    the API's IsOwnerOrReadOnly) so a non-owner gets a clean 403 page
    instead of an empty/broken form.
    """
    product = get_object_or_404(Product, pk=pk)
    if product.owner != request.user:
        return HttpResponseForbidden("You don't have permission to edit this product.")

    return render(request, 'products/edit.html', {'product': product})