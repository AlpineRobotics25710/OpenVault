// Shows only posts whose data-seasons includes the selected season tab.
let currentSeason = 'all';

function applySeasonFilter() {
    const cards = document.querySelectorAll('#posts-div [data-seasons]');
    let visible = 0;
    cards.forEach((card) => {
        const seasons = JSON.parse(card.dataset.seasons || '[]').map((s) => String(s).trim());
        const show = currentSeason === 'all' || seasons.includes(currentSeason);
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    const noResults = document.getElementById('no-season-results');
    if (noResults) noResults.classList.toggle('d-none', visible > 0 || cards.length === 0);
}

document.addEventListener('DOMContentLoaded', () => {
    const tabs = document.querySelectorAll('.season-tab');
    tabs.forEach((tab) => {
        tab.addEventListener('click', () => {
            tabs.forEach((t) => t.classList.toggle('active', t === tab));
            currentSeason = tab.dataset.season;
            applySeasonFilter();
        });
    });
});

// Re-apply after search replaces the posts.
document.addEventListener('posts-updated', applySeasonFilter);
