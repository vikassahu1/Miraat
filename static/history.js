BASE_URL = 'http://127.0.0.1:8000';

document.addEventListener('DOMContentLoaded', function() {
    let name = localStorage.getItem('username');
    // post at test-history backend
    fetch(`${BASE_URL}/test-history`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name }),
    })
     .then((response) => {
        if (!response.ok) throw new Error("Network response was not ok");
        return response.json();
      })
     .then((data) => {
        console.log('Test history posted successfully', data);
     })
        .catch((error) => {
            console.error("Error:", error);
        });
  });

