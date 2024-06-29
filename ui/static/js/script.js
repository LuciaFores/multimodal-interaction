document.addEventListener('DOMContentLoaded', function () {
    function updateTime() {
        fetch('/current_time')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-date').innerText = data.date;
                document.getElementById('current-time').innerText = data.time;
            });

        fetch('/next_medication')
            .then(response => response.json())
            .then(data => {
                if (data.time && data.medicines) {
                    let alertText = `Prossimo farmaco alle ${data.time}: `;
                    data.medicines.forEach(medicine => {
                        alertText += `${medicine[0]} (${medicine[1]}), `;
                    });
                    alertText = alertText.slice(0, -2); // Remove the last comma and space
                    document.getElementById('next-medication-alert').innerText = alertText;
                } else {
                    document.getElementById('next-medication-alert').innerText = "Nessun farmaco pianificato.";
                }
            });
    }

    updateTime();
    setInterval(updateTime, 1000); // Update every 10 seconds
});
