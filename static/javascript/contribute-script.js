function selectCategory(selectElement) {
    const category = selectElement.value;

    // Sections
    const cadSection = document.getElementById('cadSubcategory');
    const codeSection = document.getElementById('codeSubcategory');
    const cadExtra = document.getElementById('cad');
    const codeExtra = document.getElementById('code');
    const portfoliosExtra = document.getElementById('portfolio');

    // Get all input/select elements within each category section, excluding "used in comp"
    const cadInputs = cadExtra.querySelectorAll('input:not(#usedInCompCAD), select, textarea');
    const codeInputs = codeExtra.querySelectorAll('input:not(#usedInCompCode), select, textarea, input[type="file"]');
    const portfolioInputs = portfoliosExtra.querySelectorAll('input, select, textarea, input[type="file"]');

    // Reset visibility of all sections
    cadSection.classList.add('d-none');
    codeSection.classList.add('d-none');
    cadExtra.classList.add('d-none');
    codeExtra.classList.add('d-none');
    portfoliosExtra.classList.add('d-none');

    // Remove required attribute from all inputs
    [...cadInputs, ...codeInputs, ...portfolioInputs].forEach(input => {
        input.removeAttribute('required');
    });

    // Show the selected category section and set required attributes accordingly
    if (category === 'CAD') {
        cadSection.classList.remove('d-none');
        cadExtra.classList.remove('d-none');
        cadInputs.forEach(input => input.setAttribute('required', 'true'));
    } else if (category === 'Code') {
        codeSection.classList.remove('d-none');
        codeExtra.classList.remove('d-none');
        codeInputs.forEach(input => input.setAttribute('required', 'true'));
    } else if (category === 'Portfolios') {
        portfoliosExtra.classList.remove('d-none');
        portfolioInputs.forEach(input => input.setAttribute('required', 'true'));
    }
}

function validateForm() {
    const category = document.getElementById('category').value;

    if (!category) {
        alert('Please select a category.');
        return false;
    }

    // Validate subcategory for CAD and Code
    if (category === 'CAD') {
        const cadSubcategory = document.getElementById('cadSubcategorySelect').value;
        if (!cadSubcategory) {
            alert('Please select a CAD subcategory.');
            return false;
        }
    } else if (category === 'Code') {
        const codeSubcategory = document.getElementById('codeSubcategorySelect').value;
        if (!codeSubcategory) {
            alert('Please select a Code subcategory.');
            return false;
        }
    }

    return true;
}

