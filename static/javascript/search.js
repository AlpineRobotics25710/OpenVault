async function performSearch(query) {
    const form = document.getElementById('searchForm');
    const response = await fetch('/api/search', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({query, base: form.dataset.base, category: form.dataset.category}),
    });
    if (!response.ok) {
        console.error('Search failed with status', response.status);
        return;
    }
    const data = await response.json();
    document.getElementById('posts-div').innerHTML = data.html;
    document.dispatchEvent(new Event('posts-updated'));
}

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('searchForm');
    const box = document.getElementById('searchBox');
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        performSearch(box.value);
    });
    document.getElementById('clearSearchButton').addEventListener('click', () => {
        box.value = '';
        performSearch('');
    });
});
