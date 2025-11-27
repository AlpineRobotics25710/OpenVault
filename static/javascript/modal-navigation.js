// Modal navigation functionality
function navigateModal(direction, currentModalId) {
    // Get all modals on the page
    const allModals = document.querySelectorAll('.portfolio-modal');

    // Find current modal index
    let currentIndex = -1;
    allModals.forEach((modal, index) => {
        if (modal.id === currentModalId) {
            currentIndex = index;
        }
    });

    if (currentIndex === -1) return;

    // Calculate next index
    const nextIndex = currentIndex + direction;

    // Check bounds
    if (nextIndex < 0 || nextIndex >= allModals.length) return;

    // Close current modal and open next one
    const currentModal = bootstrap.Modal.getInstance(document.getElementById(currentModalId));
    if (currentModal) {
        currentModal.hide();
    }

    // Wait a moment for the close animation, then open the next modal
    setTimeout(() => {
        const nextModal = new bootstrap.Modal(allModals[nextIndex]);
        nextModal.show();

        // Update arrow states after modal is shown
        setTimeout(() => {
            updateArrowStates(allModals[nextIndex].id, nextIndex, allModals.length);
        }, 100);
    }, 300);
}

function updateArrowStates(modalId, currentIndex, totalModals) {
    const modal = document.getElementById(modalId);
    if (!modal) return;

    const prevArrow = modal.querySelector('.modal-nav-prev');
    const nextArrow = modal.querySelector('.modal-nav-next');

    // Disable/enable arrows based on position
    if (prevArrow) {
        prevArrow.disabled = currentIndex === 0;
    }

    if (nextArrow) {
        nextArrow.disabled = currentIndex === totalModals - 1;
    }
}

// Initialize arrow states when modals are shown
document.addEventListener('DOMContentLoaded', function () {
    const allModals = document.querySelectorAll('.portfolio-modal');

    allModals.forEach((modal, index) => {
        modal.addEventListener('shown.bs.modal', function () {
            updateArrowStates(modal.id, index, allModals.length);
        });
    });
});

// Add keyboard navigation (left/right arrows)
document.addEventListener('keydown', function (e) {
    // Check if a modal is currently open
    const openModal = document.querySelector('.portfolio-modal.show');
    if (!openModal) return;

    if (e.key === 'ArrowLeft') {
        const prevButton = openModal.querySelector('.modal-nav-prev');
        if (prevButton && !prevButton.disabled) {
            navigateModal(-1, openModal.id);
        }
    } else if (e.key === 'ArrowRight') {
        const nextButton = openModal.querySelector('.modal-nav-next');
        if (nextButton && !nextButton.disabled) {
            navigateModal(1, openModal.id);
        }
    }
});
