function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}


document.addEventListener('DOMContentLoaded', function () {

    const profileForm = document.getElementById('profile-form');

    if (!profileForm) {
        return;
    }


    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone_number');
    const addressInput = document.getElementById('address');
    const pictureInput = document.getElementById('display_picture');

    const currentPicture =
        document.getElementById('current-picture');

    const errorBox =
        document.getElementById('profile-error');

    const successBox =
        document.getElementById('profile-success');

    const updateButton =
        document.getElementById('update-profile-btn');


    function showError(message) {
        errorBox.textContent = message;
        errorBox.classList.remove('d-none');

        successBox.classList.add('d-none');
    }


    function showSuccess(message) {
        successBox.textContent = message;
        successBox.classList.remove('d-none');

        errorBox.classList.add('d-none');
    }


    function loadProfile() {

        fetch('/api/profile/', {
            method: 'GET',
            credentials: 'include'
        })

        .then(async response => {

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || 'Could not load profile.'
                );
            }

            return data;
        })

        .then(data => {

            usernameInput.value = data.username || '';
            emailInput.value = data.email || '';
            phoneInput.value = data.phone_number || '';
            addressInput.value = data.address || '';


            if (data.display_picture) {

                currentPicture.innerHTML = `
                    <img
                        src="${data.display_picture}"
                        alt="Profile Picture"
                        class="rounded-circle"
                        style="
                            width: 120px;
                            height: 120px;
                            object-fit: cover;
                        "
                    >
                `;

            } else {

                currentPicture.innerHTML = `
                    <div
                        class="rounded-circle bg-secondary text-white d-inline-flex align-items-center justify-content-center"
                        style="
                            width: 120px;
                            height: 120px;
                            font-size: 40px;
                        "
                    >
                        ${data.username
                            ? data.username.charAt(0).toUpperCase()
                            : '?'}
                    </div>
                `;
            }

        })

        .catch(error => {
            showError(error.message);
        });
    }


    profileForm.addEventListener('submit', function (event) {

        event.preventDefault();

        updateButton.disabled = true;
        updateButton.textContent = 'Updating...';

        errorBox.classList.add('d-none');
        successBox.classList.add('d-none');


        const formData = new FormData();

        formData.append(
            'email',
            emailInput.value
        );

        formData.append(
            'phone_number',
            phoneInput.value
        );

        formData.append(
            'address',
            addressInput.value
        );


        if (pictureInput.files.length > 0) {

            formData.append(
                'display_picture',
                pictureInput.files[0]
            );
        }


        fetch('/api/profile/', {
            method: 'PATCH',

            headers: {
                'X-CSRFToken': getCsrfToken()
            },

            credentials: 'include',

            body: formData
        })

        .then(async response => {

            const data = await response.json();

            if (!response.ok) {

                let message =
                    'Could not update profile.';

                if (data.detail) {
                    message = data.detail;
                }

                throw new Error(message);
            }

            return data;
        })

        .then(data => {

            showSuccess(
                'Profile updated successfully!'
            );


            if (data.display_picture) {

                currentPicture.innerHTML = `
                    <img
                        src="${data.display_picture}"
                        alt="Profile Picture"
                        class="rounded-circle"
                        style="
                            width: 120px;
                            height: 120px;
                            object-fit: cover;
                        "
                    >
                `;
            }

            updateButton.disabled = false;
            updateButton.textContent = 'Update Profile';
        })

        .catch(error => {

            showError(error.message);

            updateButton.disabled = false;
            updateButton.textContent = 'Update Profile';
        });
    });


    loadProfile();
});