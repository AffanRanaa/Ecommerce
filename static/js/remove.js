document.addEventListener('DOMContentLoaded', function () {

    const removeForms = document.querySelectorAll(
        '.cart-remove-form'
    );

    if (!removeForms.length) return;


    function getCSRFToken(form) {
        const csrfInput = form.querySelector(
            '[name="csrfmiddlewaretoken"]'
        );

        return csrfInput ? csrfInput.value : '';
    }


    removeForms.forEach(function (form) {

        form.addEventListener('submit', async function (event) {

            event.preventDefault();

            const itemId = form.dataset.itemId;


            try {

                const response = await fetch(
                    `/api/cart/remove/${itemId}/`,
                    {
                        method: 'POST',

                        headers: {
                            'X-CSRFToken': getCSRFToken(form)
                        },

                        credentials: 'include'
                    }
                );


                const data = await response.json();


                if (!response.ok) {
                    alert(
                        data.error ||
                        'Unable to remove cart item.'
                    );
                    return;
                }


                // Remove the item row
                const row = document.querySelector(
                    `[data-cart-row="${itemId}"]`
                );

                if (row) {
                    row.remove();
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


                // If cart becomes empty
                if (data.cart_empty) {

                    const content = document.querySelector(
                        'main'
                    ) || document.body;

                    content.innerHTML = `
                        <div class="container mt-4">
                            <h2 class="mb-4">Your Cart</h2>
                            <p class="text-muted">
                                Your cart is empty.
                            </p>
                        </div>
                    `;

                    return;
                }


            } catch (error) {

                console.error(
                    'Cart remove error:',
                    error
                );

                alert(
                    'Something went wrong while removing the item.'
                );
            }

        });

    });

});