document.addEventListener('DOMContentLoaded', function () {

    const updateForms = document.querySelectorAll('.cart-update-form');

    if (!updateForms.length) return;


    function getCSRFToken(form) {
        const csrfInput = form.querySelector(
            '[name="csrfmiddlewaretoken"]'
        );

        return csrfInput ? csrfInput.value : '';
    }


    updateForms.forEach(function (form) {

        form.addEventListener('submit', async function (event) {

            event.preventDefault();

            const itemId = form.dataset.itemId;

            const quantityInput = form.querySelector(
                '[name="quantity"]'
            );

            const quantity = quantityInput.value;


            try {

                const response = await fetch(
                    `/api/cart/update/${itemId}/`,
                    {
                        method: 'POST',

                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCSRFToken(form)
                        },

                        credentials: 'include',

                        body: JSON.stringify({
                            quantity: quantity
                        })
                    }
                );


                const data = await response.json();


                if (!response.ok) {
                    alert(
                        data.error ||
                        'Unable to update cart item.'
                    );
                    return;
                }


                // Update line total
                const lineTotal = document.querySelector(
                    `[data-line-total="${itemId}"]`
                );

                if (lineTotal) {
                    lineTotal.textContent =
                        '$' + data.line_total;
                }


                // Update subtotal
                const subtotal =
                    document.getElementById('cart-subtotal');

                if (subtotal) {
                    subtotal.textContent =
                        '$' + data.subtotal;
                }


                // Update discount
                const discount =
                    document.getElementById('cart-discount');

                if (discount) {
                    discount.textContent =
                        '- $' + data.discount_amount;
                }


                // Update total
                const total =
                    document.getElementById('cart-total');

                if (total) {
                    total.textContent =
                        '$' + data.total;
                }

            } catch (error) {

                console.error(
                    'Cart update error:',
                    error
                );

                alert(
                    'Something went wrong while updating the cart.'
                );
            }

        });

    });

});