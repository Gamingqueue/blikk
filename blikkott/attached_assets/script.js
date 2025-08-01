async function fetchCode() {
    const key = document.getElementById('keyInput').value;
    const result = document.getElementById('result');
    const response = await fetch('/get-code', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key })
    });
    const data = await response.json();
    if (data.code) {
        result.innerText = 'Your Netflix Code: ' + data.code;
    } else {
        result.innerText = 'Error: ' + data.error;
    }
}
