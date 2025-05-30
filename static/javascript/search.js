async function performSearch(query) {
    const response = await fetch('/api/search', {
        method: 'POST', headers: {
            'Content-Type': 'application/json',
        }, body: JSON.stringify({query}),
    });

    if (!response.ok) {
        const text = await response.text();
        console.error("Server returned error HTML:", text);
        return;
    }

    const data = await response.json();

    // Parse the HTML string from the server
    const parser = new DOMParser();
    const doc = parser.parseFromString(data.template, 'text/html');

    // You can either replace the full body or just a specific section
    const newBody = doc.body;

    if (newBody) {
        // Replace contents of <body> without replacing the entire document
        document.body.innerHTML = newBody.innerHTML;
        setupFormHandler()
    } else {
        console.error("Parsed HTML does not contain a <body> element.");
    }
}

function setupFormHandler() {
    const form = document.getElementById('searchForm');
    if (!form) {
        console.error("Form with id 'searchForm' not found!");
        return;
    }

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const query = document.getElementById('searchBox').value;
        await performSearch(query);
    });
}

function clearSearch() {
    document.getElementById("searchBox").value = ""; // Clear input
    document.getElementById("searchForm").submit();
}

document.addEventListener('DOMContentLoaded', setupFormHandler);
