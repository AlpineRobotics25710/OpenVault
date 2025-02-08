function selectCategory(selectElement) {
    const category = selectElement.value;
    const cadSection = document.getElementById('cadSubcategory');
    const codeSection = document.getElementById('codeSubcategory');
    const cadExtra = document.getElementById('cad');
    const codeExtra = document.getElementById('code');
    const portfoliosExtra = document.getElementById('portfolio');


    // Reset visibility of subcategories
    cadSection.classList.add('d-none');
    codeSection.classList.add('d-none');
    cadExtra.classList.add('d-none');
    codeExtra.classList.add('d-none')
    portfoliosExtra.classList.add('d-none')

    // Show respective subcategory
    if (category === 'CAD') {
        cadSection.classList.remove('d-none');
        cadExtra.classList.remove('d-none');
    } else if (category === 'Code') {
        codeSection.classList.remove('d-none');
        codeExtra.classList.remove('d-none')
    } else if (category === 'Portfolios') {
        portfoliosExtra.classList.remove('d-none')
    }
}

function validateForm() {
    const category = document.getElementById('category').value;
    if (!category) {
        alert('Please select a category.');
        return false;
    }
    return true;
}
