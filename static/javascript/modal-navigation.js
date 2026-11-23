// Prev/next navigation between post modals, skipping posts hidden by the season filter.
// Each modal directly follows its card column in the DOM (see posts.html).
function visibleModals() {
    return [...document.querySelectorAll('.portfolio-modal')]
        .filter((m) => m.previousElementSibling?.style.display !== 'none');
}

function navigateModal(direction, currentModalId) {
    const modals = visibleModals();
    const index = modals.findIndex((m) => m.id === currentModalId);
    const next = modals[index + direction];
    if (index === -1 || !next) return;

    modals[index].addEventListener('hidden.bs.modal', () => {
        bootstrap.Modal.getOrCreateInstance(next).show();
    }, {once: true});
    bootstrap.Modal.getInstance(modals[index])?.hide();
}

// Bootstrap modal events bubble, so this also covers modals added by search.
document.addEventListener('shown.bs.modal', (e) => {
    const modals = visibleModals();
    const index = modals.indexOf(e.target);
    const prev = e.target.querySelector('.modal-nav-prev');
    const next = e.target.querySelector('.modal-nav-next');
    if (prev) prev.disabled = index <= 0;
    if (next) next.disabled = index === -1 || index >= modals.length - 1;
});

document.addEventListener('keydown', (e) => {
    const open = document.querySelector('.portfolio-modal.show');
    if (!open) return;
    if (e.key === 'ArrowLeft' && !open.querySelector('.modal-nav-prev')?.disabled) {
        navigateModal(-1, open.id);
    } else if (e.key === 'ArrowRight' && !open.querySelector('.modal-nav-next')?.disabled) {
        navigateModal(1, open.id);
    }
});
