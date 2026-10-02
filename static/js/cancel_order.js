function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.querySelectorAll('.cancel-order-btn').forEach(function (button) {

    button.addEventListener('click', function () {

        const orderId = this.dataset.orderId;

        if (!confirm('Are you sure you want to cancel this order?')) {
            return;
        }

        button.disabled = true;
        button.textContent = 'Cancelling...';

        fetch(`/api/orders/${orderId}/cancel/`, {
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
                    data.detail || 'Unable to cancel the order.'
                );
            }

            return data;
        })
        .then(data => {
            alert(data.detail || 'Order cancelled successfully.');
            window.location.reload();
        })
        .catch(error => {
            alert(error.message);

            button.disabled = false;
            button.textContent = 'Cancel Order';
        });
    });

});