function getCsrfTokenForProducts() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.addEventListener('DOMContentLoaded', function () {

    const deleteBtn = document.getElementById('delete-product-btn');

    // Button only exists when the logged-in user owns the product
    if (!deleteBtn) return;

    deleteBtn.addEventListener('click', function () {

        const confirmed = confirm(
            'Are you sure you want to delete this product? This cannot be undone.'
        );

        if (!confirmed) return;

        const productId = deleteBtn.dataset.productId;

        fetch(`/api/products/${productId}/`, {
            method: 'DELETE',

            headers: {
                'X-CSRFToken': getCsrfTokenForProducts()
            },

            credentials: 'include'
        })

        .then(response => {

            if (response.status === 204) {
                // Product deleted successfully
                window.location.href = '/';
            } else {
                throw new Error('Could not delete product.');
            }

        })

        .catch(error => {
            alert(error.message);
        });

    });

});
