function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}


// ===============================
// Get product-specific URLs from HTML
// ===============================

const editProductPage = document.getElementById('edit-product-page');

if (editProductPage) {

    const productId = editProductPage.dataset.productId;
    const productDetailUrl = editProductPage.dataset.productDetailUrl;


    // ===============================
    // Delete an existing image
    // ===============================

    document.querySelectorAll('.delete-existing-image-btn').forEach(function (btn) {

        btn.addEventListener('click', function () {

            const imageId = btn.dataset.imageId;

            const confirmed = confirm('Delete this image?');

            if (!confirmed) return;

            fetch(`/api/products/${productId}/images/${imageId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'include'
            })
            .then(response => {

                if (response.status === 204) {

                    const imageCard = document.querySelector(
                        `#current-images [data-image-id="${imageId}"]`
                    );

                    if (imageCard) {
                        imageCard.remove();
                    }

                } else {

                    throw new Error('Could not delete image.');

                }

            })
            .catch(error => {
                alert(error.message);
            });

        });

    });


    // ===============================
    // Add new images
    // ===============================

    const newImagesInput = document.getElementById('new-images');
    const newImagePreview = document.getElementById('new-image-preview');

    let newSelectedFiles = [];


    newImagesInput.addEventListener('change', function () {

        newSelectedFiles = newSelectedFiles.concat(
            Array.from(this.files)
        );

        newImagesInput.value = '';

        renderNewImagePreview();

    });


    function renderNewImagePreview() {

        newImagePreview.innerHTML = '';

        newSelectedFiles.forEach(function (file, index) {

            const reader = new FileReader();

            reader.onload = function (event) {

                const col = document.createElement('div');

                col.className = 'col-4';

                col.innerHTML = `
                    <div class="card position-relative">

                        <img
                            src="${event.target.result}"
                            class="card-img-top"
                            style="height: 100px; object-fit: cover;"
                        >

                        <button
                            type="button"
                            class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-new-image-btn"
                            data-index="${index}"
                        >
                            ×
                        </button>

                    </div>
                `;

                newImagePreview.appendChild(col);


                col.querySelector(
                    '.remove-new-image-btn'
                ).addEventListener('click', function () {

                    newSelectedFiles.splice(index, 1);

                    renderNewImagePreview();

                });

            };

            reader.readAsDataURL(file);

        });

    }


    // ===============================
    // Upload new images
    // ===============================

    document.getElementById(
        'upload-new-images-btn'
    ).addEventListener('click', function () {

        const uploadErrorBox = document.getElementById(
            'upload-error'
        );

        uploadErrorBox.classList.add('d-none');


        if (newSelectedFiles.length === 0) {
            return;
        }


        const formData = new FormData();

        newSelectedFiles.forEach(function (file) {
            formData.append('images', file);
        });


        fetch(`/api/products/${productId}/upload_image/`, {

            method: 'POST',

            headers: {
                'X-CSRFToken': getCsrfToken()
            },

            credentials: 'include',

            body: formData

        })
        .then(response => {

            if (!response.ok) {
                throw new Error('Could not upload images.');
            }

            return response.json();

        })
        .then(images => {

            images.forEach(function (image) {

                const col = document.createElement('div');

                col.className = 'col-4';
                col.dataset.imageId = image.id;

                col.innerHTML = `
                    <div class="card position-relative">

                        <img
                            src="${image.image}"
                            class="card-img-top"
                            style="height: 100px; object-fit: cover;"
                        >

                        <button
                            type="button"
                            class="btn btn-sm btn-danger position-absolute top-0 end-0 delete-existing-image-btn"
                            data-image-id="${image.id}"
                        >
                            ×
                        </button>

                    </div>
                `;

                document.getElementById('current-images').appendChild(col);


                col.querySelector(
                    '.delete-existing-image-btn'
                ).addEventListener('click', function () {

                    const imageId = this.dataset.imageId;

                    const confirmed = confirm('Delete this image?');

                    if (!confirmed) return;

                    fetch(`/api/products/${productId}/images/${imageId}/`, {
                        method: 'DELETE',
                        headers: {
                            'X-CSRFToken': getCsrfToken()
                        },
                        credentials: 'include'
                    })
                    .then(response => {

                        if (response.status === 204) {
                            col.remove();
                        } else {
                            throw new Error('Could not delete image.');
                        }

                    })
                    .catch(error => {
                        alert(error.message);
                    });

                });

            });

            newSelectedFiles = [];
            newImagePreview.innerHTML = '';

        })
        .catch(error => {

            uploadErrorBox.textContent = error.message;

            uploadErrorBox.classList.remove('d-none');

        });

    });


    // ===============================
    // Save text-field changes
    // ===============================

    document.getElementById(
        'edit-product-form'
    ).addEventListener('submit', function (event) {

        event.preventDefault();


        const errorBox = document.getElementById(
            'form-error'
        );

        errorBox.classList.add('d-none');


        const updatedData = {

            title: document.getElementById(
                'title'
            ).value,

            description: document.getElementById(
                'description'
            ).value,

            price: document.getElementById(
                'price'
            ).value,

            stock_quantity: document.getElementById(
                'stock_quantity'
            ).value

        };


        fetch(`/api/products/${productId}/`, {

            method: 'PATCH',

            headers: {

                'Content-Type': 'application/json',

                'X-CSRFToken': getCsrfToken()

            },

            credentials: 'include',

            body: JSON.stringify(updatedData)

        })
        .then(response => {

            if (!response.ok) {

                throw new Error(
                    'Could not update product. Check your inputs.'
                );

            }

            return response.json();

        })
        .then(() => {

            window.location.href = productDetailUrl;

        })
        .catch(error => {

            errorBox.textContent = error.message;

            errorBox.classList.remove('d-none');

        });

    });

}