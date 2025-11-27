// FTC Season definitions (most recent first)
const FTC_SEASONS = [
    { id: 'all', name: 'All Seasons', year: null },
    { id: '2024-2025', name: 'INTO THE DEEP℠', year: '2024-2025' },
    { id: '2023-2024', name: 'CENTERSTAGE℠', year: '2023-2024' },
    { id: '2022-2023', name: 'POWERPLAY℠', year: '2022-2023' },
    { id: '2021-2022', name: 'FREIGHT FRENZY℠', year: '2021-2022' },
    { id: '2020-2021', name: 'ULTIMATE GOAL℠', year: '2020-2021' },
    { id: '2019-2020', name: 'SKYSTONE℠', year: '2019-2020' },
    { id: '2018-2019', name: 'ROVER RUCKUS℠', year: '2018-2019' },
    { id: '2017-2018', name: 'RELIC RECOVERY℠', year: '2017-2018' },
    { id: '2016-2017', name: 'VELOCITY VORTEX℠', year: '2016-2017' },
    { id: '2015-2016', name: 'RES-Q℠', year: '2015-2016' }
];

let currentSeason = 'all';
let allCards = [];

function initializeSeasonFilter() {
    // Store all cards initially
    allCards = Array.from(document.querySelectorAll('#posts-div .col.mb-5'));
    console.log('Initialized season filter. Found', allCards.length, 'cards');

    // Set up tab click handlers
    const seasonTabs = document.querySelectorAll('.season-tab');
    seasonTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            e.preventDefault();
            const seasonId = tab.dataset.season;
            filterBySeason(seasonId);

            // Update active tab
            seasonTabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
        });
    });
}

function filterBySeason(seasonId) {
    currentSeason = seasonId;
    console.log('=== FILTER BY SEASON ===');
    console.log('Season ID:', seasonId);
    console.log('Total cards:', allCards.length);

    if (seasonId === 'all') {
        // Show all cards
        allCards.forEach(card => {
            card.style.display = '';
        });
        updateNoResultsMessage(false);
        return;
    }

    let visibleCount = 0;
    let debugInfo = [];

    // Filter cards based on season
    allCards.forEach((card, index) => {
        // Find the button that triggers the modal
        const button = card.querySelector('[data-bs-toggle="modal"]');

        if (!button) {
            console.log(`Card ${index}: No modal button found`);
            card.style.display = 'none';
            return;
        }

        // Get the modal ID from the button's data-bs-target
        const modalId = button.getAttribute('data-bs-target');
        if (!modalId) {
            console.log(`Card ${index}: No modal ID found`);
            card.style.display = 'none';
            return;
        }

        // Find the actual modal element
        const modal = document.querySelector(modalId);
        if (!modal) {
            console.log(`Card ${index}: Modal ${modalId} not found`);
            card.style.display = 'none';
            return;
        }

        // Get seasons_used from the modal content
        const seasonsUsedElement = modal.querySelector('[data-seasons-used]');
        let seasonsUsed = [];

        if (seasonsUsedElement) {
            const rawData = seasonsUsedElement.dataset.seasonsUsed;
            try {
                seasonsUsed = JSON.parse(rawData || '[]');
                if (index < 3) {
                    debugInfo.push({
                        cardIndex: index,
                        modalId: modalId,
                        rawData: rawData,
                        seasonsUsed: seasonsUsed,
                        match: seasonsUsed.includes(seasonId)
                    });
                }
            } catch (e) {
                console.error('Failed to parse seasons data:', rawData, e);
            }
        } else {
            if (index < 3) {
                console.log(`Card ${index}: No data-seasons-used element found in modal`);
            }
        }

        // Check if this season is in the seasons_used array
        const shouldShow = seasonsUsed.some(season => {
            // Handle different season formats
            const normalizedSeason = String(season).trim();
            return normalizedSeason === seasonId;
        });

        if (shouldShow) {
            card.style.display = '';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });

    console.log('Debug info (first 3 cards):', debugInfo);
    console.log('Visible count:', visibleCount);
    console.log('=========================');
    updateNoResultsMessage(visibleCount === 0);
}

function updateNoResultsMessage(show) {
    let noResultsDiv = document.querySelector('.no-season-results');

    if (show) {
        if (!noResultsDiv) {
            const container = document.querySelector('#posts-div .row');
            noResultsDiv = document.createElement('div');
            noResultsDiv.className = 'col-12 text-center no-season-results';
            noResultsDiv.innerHTML = `
                <div class="card">
                    <div class="card-body p-5">
                        <h5 class="fw-bolder">No posts found for this season</h5>
                        <p class="text-muted">Try selecting a different season or view all seasons.</p>
                    </div>
                </div>
            `;
            container.appendChild(noResultsDiv);
        }
        noResultsDiv.style.display = '';
    } else {
        if (noResultsDiv) {
            noResultsDiv.style.display = 'none';
        }
    }
}

// Re-initialize after search results update
function reinitializeAfterSearch() {
    allCards = Array.from(document.querySelectorAll('#posts-div .col.mb-5'));
    if (currentSeason !== 'all') {
        filterBySeason(currentSeason);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeSeasonFilter);

// Re-initialize after search (hook into existing search functionality)
const originalPerformSearch = window.performSearch;
if (originalPerformSearch) {
    window.performSearch = async function (...args) {
        await originalPerformSearch.apply(this, args);
        setTimeout(reinitializeAfterSearch, 100);
    };
}
