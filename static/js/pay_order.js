function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.querySelectorAll('.pay-order-btn').forEach(function (button) {

    button.addEventListener('click', function () {

        const orderId = this.dataset.orderId;

        button.disabled = true;
        button.textContent = 'Redirecting to payment...';

        fetch(`/api/orders/${orderId}/pay/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        })
        .then(async response => {
            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 'Unable to start payment.'
                );
            }

            return data;
        })
        .then(data => {
            window.location.href = data.checkout_url;
        })
        .catch(error => {
            alert(error.message);

            button.disabled = false;
            button.textContent = 'Pay Order';
        });

    });

});