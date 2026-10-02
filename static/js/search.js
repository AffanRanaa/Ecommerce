document.addEventListener('DOMContentLoaded', function () {
    const searchInput = document.getElementById('live-search-input');
    if (!searchInput) return;

    const resultsBox = document.getElementById('search-results');
    let debounceTimer;

    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const query = searchInput.value.trim();

        if (query.length === 0) {
            resultsBox.innerHTML = '';
            resultsBox.classList.add('d-none');
            return;
        }

        // debounce: wait 300ms after the user stops typing before calling the API,
        // so we don't fire a request on every single keystroke
        debounceTimer = setTimeout(() => {
            fetch(`/api/search/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(products => {
                    resultsBox.innerHTML = '';
                    if (products.length === 0) {
                        resultsBox.innerHTML = '<div class="list-group-item text-muted">No results</div>';
                    } else {
                        products.forEach(product => {
                            const item = document.createElement('a');
                            item.href = `/products/${product.id}/`;
                            item.className = 'list-group-item list-group-item-action';
                            item.textContent = `${product.title} — $${product.price}`;
                            resultsBox.appendChild(item);
                        });
                    }
                    resultsBox.classList.remove('d-none');
                });
        }, 300);
    });

    // hide the dropdown when clicking anywhere outside it
    document.addEventListener('click', function (event) {
        if (!resultsBox.contains(event.target) && event.target !== searchInput) {
            resultsBox.classList.add('d-none');
        }
    });
});