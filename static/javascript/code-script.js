function selectYear(year) {
    document.getElementById('selectedYear').value = year;
    //document.getElementById('yearDropdownButton').textContent = year;
    document.getElementById('filterForm').submit();
}

function selectUsedInComp(usedInComp) {
    document.getElementById('usedInComp').value = usedInComp;
    document.getElementById('filterForm').submit();
}

function selectTeamNumber(teamNumber) {
    document.getElementById('selectedTeamNumber').value = teamNumber;
    document.getElementById('filterForm').submit();
}

function selectLanguage(language) {
    document.getElementById('selectedLanguage').value = language;
    document.getElementById('filterForm').submit();
}
