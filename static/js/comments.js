// Reads the CSRF token Django sets as a cookie.
function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}

document.addEventListener('DOMContentLoaded', function () {

    const commentsList = document.getElementById('comments-list');
    const postBtn = document.getElementById('post-comment-btn');

    if (!commentsList) return;

    // ===============================
    // Post Comment
    // ===============================
    if (postBtn) {

        postBtn.addEventListener('click', function () {

            const productId = postBtn.dataset.productId;
            const bodyField = document.getElementById('comment-body');
            const body = bodyField.value.trim();

            if (!body) return;

            fetch(`/api/products/${productId}/comments/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'include',
                body: JSON.stringify({ body: body })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Could not post comment');
                }

                return response.json();
            })
            .then(comment => {

                // Build the new comment without reloading the page.
                const newComment = document.createElement('div');

                newComment.className = 'border-bottom py-2';
                newComment.dataset.commentId = comment.id;

                newComment.innerHTML = `
                    <strong></strong>
                    <p class="mb-1 comment-body-text"></p>
                    <button
                        type="button"
                        class="btn btn-sm btn-link p-0 me-2 edit-comment-btn"
                    >
                        Edit
                    </button>
                    <button
                        type="button"
                        class="btn btn-sm btn-link text-danger p-0 delete-comment-btn"
                    >
                        Delete
                    </button>
                `;

                newComment.querySelector('strong').textContent = comment.author;
                newComment.querySelector('.comment-body-text').textContent = comment.body;

                commentsList.prepend(newComment);

                bodyField.value = '';
            })
            .catch(error => alert(error.message));
        });
    }

    // ===============================
    // Edit / Delete
    // Event delegation allows this to
    // work for newly added comments too.
    // ===============================
    commentsList.addEventListener('click', function (event) {

        // ===============================
        // DELETE
        // ===============================
        if (event.target.classList.contains('delete-comment-btn')) {

            const commentDiv = event.target.closest('[data-comment-id]');
            const commentId = commentDiv.dataset.commentId;

            const confirmed = confirm('Delete this comment?');

            if (!confirmed) return;

            fetch(`/api/comments/${commentId}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': getCsrfToken()
                },
                credentials: 'include'
            })
            .then(response => {

                if (response.status === 204) {
                    commentDiv.remove();
                } else {
                    throw new Error('Could not delete comment.');
                }

            })
            .catch(error => alert(error.message));
        }

        // ===============================
        // EDIT
        // ===============================
        if (event.target.classList.contains('edit-comment-btn')) {

            const commentDiv = event.target.closest('[data-comment-id]');
            const commentId = commentDiv.dataset.commentId;

            const bodyEl = commentDiv.querySelector('.comment-body-text');
            const currentText = bodyEl.textContent;

            commentDiv
                .querySelector('.edit-comment-btn')
                .classList.add('d-none');

            commentDiv
                .querySelector('.delete-comment-btn')
                .classList.add('d-none');

            const editArea = document.createElement('div');

            editArea.className = 'edit-comment-area';

            editArea.innerHTML = `
                <textarea class="form-control form-control-sm mb-1">${currentText}</textarea>
                <button
                    type="button"
                    class="btn btn-sm btn-primary save-comment-btn"
                >
                    Save
                </button>
                <button
                    type="button"
                    class="btn btn-sm btn-secondary cancel-comment-btn"
                >
                    Cancel
                </button>
            `;

            bodyEl.classList.add('d-none');
            commentDiv.appendChild(editArea);

            // Cancel edit
            editArea
                .querySelector('.cancel-comment-btn')
                .addEventListener('click', function () {

                    editArea.remove();

                    bodyEl.classList.remove('d-none');

                    commentDiv
                        .querySelector('.edit-comment-btn')
                        .classList.remove('d-none');

                    commentDiv
                        .querySelector('.delete-comment-btn')
                        .classList.remove('d-none');
                });

            // Save edit
            editArea
                .querySelector('.save-comment-btn')
                .addEventListener('click', function () {

                    const newText = editArea
                        .querySelector('textarea')
                        .value
                        .trim();

                    if (!newText) return;

                    fetch(`/api/comments/${commentId}/`, {
                        method: 'PATCH',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': getCsrfToken()
                        },
                        credentials: 'include',
                        body: JSON.stringify({ body: newText })
                    })
                    .then(response => {

                        if (!response.ok) {
                            throw new Error('Could not update comment.');
                        }

                        return response.json();
                    })
                    .then(updatedComment => {

                        bodyEl.textContent = updatedComment.body;

                        editArea.remove();

                        bodyEl.classList.remove('d-none');

                        commentDiv
                            .querySelector('.edit-comment-btn')
                            .classList.remove('d-none');

                        commentDiv
                            .querySelector('.delete-comment-btn')
                            .classList.remove('d-none');
                    })
                    .catch(error => alert(error.message));
                });
        }
    });
});