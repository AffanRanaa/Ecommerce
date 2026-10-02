function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

const checkoutPage = document.getElementById('checkout-page');

if (checkoutPage) {

    const checkoutBtn = document.getElementById('checkout-btn');
    const errorBox = document.getElementById('checkout-error');

    const couponCode = checkoutPage.dataset.couponCode;
    const orderHistoryUrl = checkoutPage.dataset.orderHistoryUrl;

    // When this page is restored from the browser's back-forward cache
    // (e.g. user hits Back after reaching Stripe's page without paying),
    // reset the button so it is clickable again.
    window.addEventListener('pageshow', function (event) {
        checkoutBtn.disabled = false;
        checkoutBtn.textContent = 'Proceed to Checkout';
    });

    checkoutBtn.addEventListener('click', function () {
        checkoutBtn.disabled = true;
        checkoutBtn.textContent = 'Redirecting to payment...';

        fetch('/api/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            credentials: 'include',
            body: JSON.stringify(
                couponCode
                    ? { coupon_code: couponCode }
                    : {}
            )
        })
        .then(async response => {
            const data = await response.json();

            if (!response.ok) {
                const error = new Error(
                    data.stock ||
                    data.detail ||
                    'Checkout failed. Please try again.'
                );

                error.stock = data.stock || null;
                error.priceChanged = data.price_changed || false;
                error.orderId = data.order_id || null;
                error.items = data.items || [];

                throw error;
            }

            return data;
        })
        .then(data => {
            window.location.href = data.checkout_url;
        })
        .catch(error => {

            if (error.stock) {

                errorBox.innerHTML = `
                    <strong>⚠️ Stock Unavailable</strong>
                `;

            } else if (error.priceChanged) {

                let message = `
                    <strong>⚠️ Price Change Detected</strong><br>
                    The price of one or more products in your pending order
                    has changed.
                    <br><br>
                    Please either <strong>pay for your pending order</strong>
                    at its original locked price or
                    <strong>cancel the pending order</strong> before creating
                    a new order.
                `;

                if (error.items && error.items.length > 0) {
                    message += `
                        <hr>
                        <strong>Affected products:</strong>
                        <ul class="mb-0">
                    `;

                    error.items.forEach(item => {
                        message += `
                            <li>
                                ${item.product_title}:
                                $${item.old_price}
                                → $${item.current_price}
                            </li>
                        `;
                    });

                    message += '</ul>';
                }

                message += `
                    <hr>
                    <a href="${orderHistoryUrl}"
                       class="btn btn-sm btn-danger mt-1">
                        Go to My Orders
                    </a>
                `;

                errorBox.innerHTML = message;

            } else {
                errorBox.textContent = error.message;
            }

            errorBox.classList.remove('d-none');

            checkoutBtn.disabled = false;
            checkoutBtn.textContent = 'Proceed to Checkout';
        });
    });
}
