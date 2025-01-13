function selectYear(year) {
    document.getElementById('selectedYear').value = year;
    //document.getElementById('yearDropdownButton').textContent = year;
    document.getElementById('filterForm').submit();
}

function selectTeamNumber(teamNumber) {
    document.getElementById('selectedTeamNumber').value = teamNumber;
    document.getElementById('filterForm').submit();
}

function selectAwardWon(awardWon) {
    document.getElementById('selectedAwardWon').value = awardWon;
    document.getElementById('filterForm').submit();
}
