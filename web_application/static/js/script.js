/**
 * This script sets up the front-end behavior for updating time, 
 * displaying medication alerts, and handling background changes via Socket.IO events.
 */

document.addEventListener('DOMContentLoaded', function () {
    
    /**
     * Fetches the current time and the next medication information from the server.
     * Updates the relevant elements in the DOM with this information.
     */
    function updateTime() {
        // Fetch current date and time
        fetch('/current_time')
            .then(response => response.json())
            .then(data => {
                document.getElementById('current-date').innerText = data.date;
                document.getElementById('current-time').innerText = data.time;
            });

        // Fetch next medication time and details
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

    // Initial call to update time and set an interval to update every 1 second
    updateTime();
    setInterval(updateTime, 1000);

    // Setup Socket.IO connection
    const socket = io();

    /**
     * Listener for 'background_event_change' event from Socket.IO.
     * Changes the background image and hides specific elements.
     * @param {Object} data - Contains the image filename to be set as background.
     */
    socket.on('background_event_change', function (data) {
        const backgroundImageDiv = document.getElementById('background-image');
        backgroundImageDiv.style.backgroundImage = `url('/static/images/${data.image}')`;
        document.getElementById('therapy-plan').style.display = 'none';
        document.getElementById('clock-widget').style.display = 'none';
        document.getElementById('alert').style.display = 'none';
        document.getElementById('alert-medication').style.display = 'none';
    });

    /**
     * Listener for 'background_idle_change' event from Socket.IO.
     * Changes the background image and shows specific elements.
     * @param {Object} data - Contains the image filename to be set as background.
     */
    socket.on('background_idle_change', function (data) {
        const backgroundImageDiv = document.getElementById('background-image');
        backgroundImageDiv.style.backgroundImage = `url('/static/images/${data.image}')`;
        document.getElementById('therapy-plan').style.display = '';
        document.getElementById('clock-widget').style.display = '';
        document.getElementById('alert').style.display = '';
        document.getElementById('alert-medication').style.display = '';
    });
});
