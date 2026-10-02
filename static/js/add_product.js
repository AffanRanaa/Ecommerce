const addProductPage = document.getElementById('add-product-page');

if (addProductPage) {

    const productListUrl = addProductPage.dataset.productListUrl;
    const productDetailUrl = addProductPage.dataset.productDetailUrl;

    const imageInput = document.getElementById('images');
    const imagePreview = document.getElementById('image-preview');

    // Accumulates files across multiple "Choose File" clicks instead of
    // letting each click replace the previous selection.
    let selectedFiles = [];

    imageInput.addEventListener('change', function () {
        selectedFiles = selectedFiles.concat(Array.from(this.files));

        // Reset so the same file can be re-picked later if removed.
        imageInput.value = '';

        renderPreview();
    });

    function renderPreview() {
        imagePreview.innerHTML = '';

        selectedFiles.forEach(function (file, index) {
            if (!file.type.startsWith('image/')) return;

            const reader = new FileReader();

            reader.onload = function (event) {
                const col = document.createElement('div');
                col.className = 'col-6 col-md-4';

                col.innerHTML = `
                    <div class="card position-relative">
                        <img
                            src="${event.target.result}"
                            class="card-img-top"
                            style="height: 150px; object-fit: cover;"
                        >
                        <button
                            type="button"
                            class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-image-btn"
                            data-index="${index}"
                        >
                            ×
                        </button>
                    </div>
                `;

                imagePreview.appendChild(col);

                col.querySelector('.remove-image-btn').addEventListener('click', function () {
                    selectedFiles.splice(index, 1);
                    renderPreview();
                });
            };

            reader.readAsDataURL(file);
        });
    }

    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');

            for (let cookie of cookies) {
                cookie = cookie.trim();

                if (cookie.substring(0, name.length + 1) === name + '=') {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }

    document.getElementById('product-form').addEventListener('submit', async function (event) {
        event.preventDefault();

        const submitButton = document.getElementById('submit-btn');
        const errorBox = document.getElementById('form-error');
        const successBox = document.getElementById('form-success');

        submitButton.disabled = true;
        submitButton.textContent = 'Creating Product...';

        errorBox.classList.add('d-none');
        successBox.classList.add('d-none');

        const productData = {
            title: document.getElementById('title').value,
            description: document.getElementById('description').value,
            price: document.getElementById('price').value,
            stock_quantity: document.getElementById('stock_quantity').value
        };

        try {

            // Step 1: Create the product
            const productResponse = await fetch(productListUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                credentials: 'include',
                body: JSON.stringify(productData)
            });

            const productResult = await productResponse.json();

            if (!productResponse.ok) {
                throw new Error(JSON.stringify(productResult));
            }

            const productId = productResult.id;

            // Step 2: Upload ALL selected images in a single request
            if (selectedFiles.length > 0) {

                const formData = new FormData();

                selectedFiles.forEach(function (file) {
                    formData.append('images', file);
                });

                const imageResponse = await fetch(
                    `/api/products/${productId}/upload_image/`,
                    {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        },
                        credentials: 'include',
                        body: formData
                    }
                );

                const imageResult = await imageResponse.json();

                if (!imageResponse.ok) {
                    throw new Error(JSON.stringify(imageResult));
                }
            }

            successBox.textContent = 'Product added successfully!';
            successBox.classList.remove('d-none');

            submitButton.textContent = 'Product Added';

            setTimeout(function () {
                window.location.href = productDetailUrl.replace(
                    '/0/',
                    `/${productId}/`
                );
            }, 800);

        } catch (error) {

            console.error(error);

            errorBox.textContent = error.message;

            errorBox.classList.remove('d-none');

            submitButton.disabled = false;
            submitButton.textContent = 'Add Product';
        }
    });
}