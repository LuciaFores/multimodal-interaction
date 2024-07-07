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
                if (data.time && data.medications) {
                    let alertText = `Prossimo farmaco alle ${data.time}: `;
                    data.medications.forEach(medication => {
                        alertText += `${medication[0]} (${medication[1]}), `;
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

    // Setup Socket.IO
    const socket = io();

    // Listen for background change events
    socket.on('background_event_change', function (data) {
        const backgroundImageDiv = document.getElementById('background-image');
        backgroundImageDiv.style.backgroundImage = `url('/static/images/${data.image}')`;
        var therapyPlanElement = document.getElementById('therapy-plan');
        therapyPlanElement.style.display = 'none';
        var clockWidgetElement = document.getElementById('clock-widget');
        clockWidgetElement.style.display = 'none';
        var alertElement = document.getElementById('alert');
        alertElement.style.display = 'none';
        var alertMedicationElement = document.getElementById('alert-medication');
        alertMedicationElement.style.display = 'none';
    });

    socket.on('background_idle_change', function (data) {
        const backgroundImageDiv = document.getElementById('background-image');
        backgroundImageDiv.style.backgroundImage = `url('/static/images/${data.image}')`;
        var therapyPlanElement = document.getElementById('therapy-plan');
        therapyPlanElement.style.display = '';
        var clockWidgetElement = document.getElementById('clock-widget');
        clockWidgetElement.style.display = '';
        var alertElement = document.getElementById('alert');
        alertElement.style.display = '';
        var alertMedicationElement = document.getElementById('alert-medication');
        alertMedicationElement.style.display = '';
    });
});
