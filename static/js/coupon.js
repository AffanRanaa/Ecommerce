document.addEventListener('DOMContentLoaded', function () {

    const couponSection = document.getElementById('coupon-section');

    if (!couponSection) return;


    function getCSRFToken() {
        const csrfInput = document.querySelector(
            '[name=csrfmiddlewaretoken]'
        );

        return csrfInput ? csrfInput.value : '';
    }


    function updateTotals(data) {
        document.getElementById('cart-subtotal').textContent =
            '$' + data.subtotal;

        document.getElementById('cart-discount').textContent =
            '- $' + data.discount_amount;

        document.getElementById('cart-total').textContent =
            '$' + data.total;
    }


    function attachCouponEvents() {

        const couponForm =
            document.getElementById('coupon-form');

        const removeCouponForm =
            document.getElementById('remove-coupon-form');


        // Apply coupon
        if (couponForm) {

            couponForm.addEventListener('submit', async function (event) {

                event.preventDefault();

                const input =
                    couponForm.querySelector('[name="coupon_code"]');

                const couponCode = input.value.trim();

                if (!couponCode) return;


                const response = await fetch(
                    '/api/cart/apply-coupon/',
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken()
                        },

                        credentials: 'include',

                        body: JSON.stringify({
                            coupon_code: couponCode
                        })
                    }
                );


                const data = await response.json();


                if (!response.ok) {
                    alert(data.error || 'Unable to apply coupon.');
                    return;
                }


                updateTotals(data);


                // Update discount label
                const discountRow =
                    document.getElementById('discount-row');

                discountRow.classList.remove('d-none');

                document.getElementById('discount-label').textContent =
                    `Discount (${data.coupon_percent}%)`;


                // Replace coupon form with applied coupon UI
                couponSection.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center mb-3">

                        <span
                            id="coupon-message"
                            class="badge bg-success"
                        >
                            Coupon "${data.coupon_code}" applied
                        </span>

                        <form
                            method="POST"
                            id="remove-coupon-form"
                        >
                            <input
                                type="hidden"
                                name="csrfmiddlewaretoken"
                                value="${getCSRFToken()}"
                            >

                            <button
                                type="submit"
                                class="btn btn-sm btn-link text-danger p-0"
                            >
                                Remove
                            </button>
                        </form>

                    </div>
                `;


                // Update checkout coupon
                const checkoutPage =
                    document.getElementById('checkout-page');

                if (checkoutPage) {
                    checkoutPage.dataset.couponCode =
                        data.coupon_code;
                }


                // New remove form needs its event listener
                attachCouponEvents();
            });
        }


        // Remove coupon
        if (removeCouponForm) {

            removeCouponForm.addEventListener('submit', async function (event) {

                event.preventDefault();


                const response = await fetch(
                    '/api/cart/remove-coupon/',
                    {
                        method: 'POST',

                        headers: {
                            'X-CSRFToken': getCSRFToken()
                        },

                        credentials: 'include'
                    }
                );


                const data = await response.json();


                if (!response.ok) {
                    alert(data.error || 'Unable to remove coupon.');
                    return;
                }


                updateTotals(data);


                // Hide discount row
                const discountRow =
                    document.getElementById('discount-row');

                discountRow.classList.add('d-none');


                // Replace applied coupon UI with coupon input
                couponSection.innerHTML = `
                    <form
                        method="POST"
                        class="d-flex mb-3"
                        id="coupon-form"
                    >
                        <input
                            type="hidden"
                            name="csrfmiddlewaretoken"
                            value="${getCSRFToken()}"
                        >

                        <input
                            type="text"
                            name="coupon_code"
                            class="form-control"
                            placeholder="Coupon code"
                        >

                        <button
                            type="submit"
                            class="btn btn-outline-primary ms-1"
                        >
                            Apply
                        </button>
                    </form>
                `;


                // Remove coupon from checkout data
                const checkoutPage =
                    document.getElementById('checkout-page');

                if (checkoutPage) {
                    checkoutPage.dataset.couponCode = '';
                }


                // New apply form needs its event listener
                attachCouponEvents();
            });
        }
    }


    attachCouponEvents();

});