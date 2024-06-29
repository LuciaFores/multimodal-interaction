document.addEventListener('DOMContentLoaded', function () {
    function updateTime() {
        fetch('/current_time')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-date').innerText = data.date;
                document.getElementById('current-time').innerText = data.time;
            });
    }

    updateTime();
    setInterval(updateTime, 1000);

    // Function to find the next medication time
    function updateNextMedication() {
        // Logic to find the next medication from the therapy plan
        // You need to implement this based on the current time and the therapy plan
    }

    updateNextMedication();
    setInterval(updateNextMedication, 60000); // Update every minute
});
