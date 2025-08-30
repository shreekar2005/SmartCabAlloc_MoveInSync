document.addEventListener('DOMContentLoaded', (event) => {
    const map = L.map('map').setView([26.4715, 73.1134], 15);
    const statusMessage = document.getElementById('status-message');
    const requestTripBtn = document.getElementById('request-trip-btn');
    const finishTripBtn = document.getElementById('finish-trip-btn'); // ADD THIS LINE
    
    let myLocationMarker = null;
    let allocatedCabMarker = null;
    let tripLine = null;
    let myTripId = null;
    let myCabId = null;
    const otherCabMarkers = {};

    // --- Helper function to read a cookie by name ---
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // --- Initial check for user authentication ---
    if (typeof userPublicId === 'undefined' || !userPublicId) {
        console.log('User not authenticated, redirecting to login.');
        window.location.href = '/auth/employee/login';
        return; // Stop execution
    }
    console.log('User Public ID:', userPublicId);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // --- Custom Icons ---
    const createIcon = (color) => L.icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });
    const icons = {
        myLocation: createIcon('blue'),
        onTripOther: createIcon('yellow'),
        myCab: createIcon('red')
    };

    // --- Map Legend ---
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        const items = {
            'My Location': 'blue',
            'Other Cabs on Trip': 'yellow',
            'My Cab': 'red'
        };
        let labels = '<strong>Legend</strong><br>';
        for (const item in items) {
            labels += `<i style="background-image: url(https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${items[item]}.png); background-size: contain; display: inline-block; width: 12px; height: 20px; vertical-align: middle;"></i> ${item}<br>`;
        }
        div.innerHTML = labels;
        return div;
    };
    legend.addTo(map);

    // --- Initial Drawing ---
    if (typeof userLocation !== 'undefined' && userLocation.lat && userLocation.lon) {
        myLocationMarker = L.marker([userLocation.lat, userLocation.lon], { icon: icons.myLocation })
            .addTo(map)
            .bindPopup('My Location').openPopup();
        map.setView([userLocation.lat, userLocation.lon], 15);
    }

    if (typeof onTripCabs !== 'undefined') {
        onTripCabs.forEach(cab => {
            if (cab.id !== myCabId && cab.status == "on_trip") {
                otherCabMarkers[cab.id] = L.marker([cab.current_lat, cab.current_lon], { icon: icons.onTripOther })
                    .addTo(map)
                    .bindPopup(`Cab ID: ${cab.id}<br>Status: On Trip`);
            }
        });
    }

    // MODIFIED SECTION: Manage button visibility on page load
    if (typeof allocatedCab !== 'undefined' && allocatedCab) {
        myCabId = allocatedCab.id;
        myTripId = allocatedCab.trip_id; // Make sure trip_id is passed from backend
        allocatedCabMarker = L.marker([allocatedCab.current_lat, allocatedCab.current_lon], { icon: icons.myCab })
            .addTo(map)
            .bindPopup(`My Cab<br>ID: ${allocatedCab.id}`);
        tripLine = L.polyline([myLocationMarker.getLatLng(), allocatedCabMarker.getLatLng()], { color: '#FF0000' }).addTo(map);
        statusMessage.textContent = `Cab ${myCabId} is on the way!`;

        requestTripBtn.style.display = 'none';
        finishTripBtn.style.display = 'block';
    }

    // --- Request Trip Button ---
    requestTripBtn.addEventListener('click', async () => {
        if (!myLocationMarker) {
            statusMessage.textContent = 'Error: My location not set.';
            return;
        }
        statusMessage.textContent = 'Requesting trip...';
        requestTripBtn.disabled = true;

        try {
            const csrfToken = getCookie('csrf_access_token');
            const response = await fetch('/employee/request-trip', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                credentials: 'include',
                body: JSON.stringify({ lat: myLocationMarker.getLatLng().lat, lon: myLocationMarker.getLatLng().lng })
            });

            const data = await response.json();
            if (response.ok) {
                myTripId = data.trip_id;
                statusMessage.textContent = `Trip Requested (ID: ${myTripId}). Waiting for allocation.`;
            } else {
                statusMessage.textContent = `Error: ${data.message || data.msg}`;
                requestTripBtn.disabled = false;
            }
        } catch (error) {
            statusMessage.textContent = 'An unexpected error occurred.';
            console.error('Request failed:', error);
            requestTripBtn.disabled = false;
        }
    });

    // ADD THIS ENTIRE BLOCK: Listener for the Finish Trip button
    finishTripBtn.addEventListener('click', async () => {
        if (!myTripId) {
            alert('Error: No active trip ID found.');
            return;
        }
        finishTripBtn.disabled = true;
        finishTripBtn.textContent = 'Finishing...';
        
        try {
            const csrfToken = getCookie('csrf_access_token');
            const response = await fetch(`/employee/trips/${myTripId}/finish`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });

            if (response.ok) {
                statusMessage.textContent = 'Trip completed! You can now request a new trip.';
                
                // Reset UI to initial state
                requestTripBtn.style.display = 'block';
                requestTripBtn.disabled = false;
                finishTripBtn.style.display = 'none';
                finishTripBtn.disabled = false;
                finishTripBtn.textContent = 'Finish My Trip';

                // Clean up map
                if (allocatedCabMarker) map.removeLayer(allocatedCabMarker);
                if (tripLine) map.removeLayer(tripLine);

                // Reset state variables
                myTripId = null;
                myCabId = null;
                allocatedCabMarker = null;
                tripLine = null;
            } else {
                const data = await response.json();
                alert(`Error: ${data.message || 'Could not finish trip.'}`);
                finishTripBtn.disabled = false;
                finishTripBtn.textContent = 'Finish My Trip';
            }
        } catch (error) {
            console.error('Finish trip failed:', error);
            alert('An unexpected error occurred.');
            finishTripBtn.disabled = false;
            finishTripBtn.textContent = 'Finish My Trip';
        }
    });

    // --- WebSocket Event Handlers ---
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', () => console.log('Connected to WebSocket for employee dashboard.'));

    // MODIFIED SECTION: Handle button visibility on trip allocation
    socket.on('trip_allocated', (data) => {
        if (data.employee_id === userPublicId) {
            console.log('My trip has been allocated!:', data);
            myCabId = data.cab_id;
            myTripId = data.trip_id;
            statusMessage.textContent = `Cab ${myCabId} is on the way!`;

            const cabLatLng = [data.cab_lat, data.cab_lon];
            if (allocatedCabMarker) {
                allocatedCabMarker.setLatLng(cabLatLng).setIcon(icons.myCab);
            } else {
                allocatedCabMarker = L.marker(cabLatLng, { icon: icons.myCab })
                    .addTo(map)
                    .bindPopup(`My Cab<br>ID: ${myCabId}`);
            }
            
            if (tripLine) {
                tripLine.setLatLngs([myLocationMarker.getLatLng(), cabLatLng]);
            } else {
                tripLine = L.polyline([myLocationMarker.getLatLng(), cabLatLng], { color: '#FF0000' }).addTo(map);
            }

            requestTripBtn.style.display = 'none';
            finishTripBtn.style.display = 'block';
        }
    });

    socket.on('location_update', (data) => {
        const { cab_id, lat, lon, status } = data;
        const cabLatLng = [lat, lon];

        if (cab_id === myCabId) {
            if (allocatedCabMarker) {
                allocatedCabMarker.setLatLng(cabLatLng);
                if (tripLine) {
                    tripLine.setLatLngs([myLocationMarker.getLatLng(), cabLatLng]);
                }
            }
        } 
        else {
            if (status === 'on_trip') {
                if (otherCabMarkers[cab_id]) {
                    otherCabMarkers[cab_id].setLatLng(cabLatLng);
                } 
                else {
                    otherCabMarkers[cab_id] = L.marker(cabLatLng, { icon: icons.onTripOther })
                        .addTo(map)
                        .bindPopup(`Cab ID: ${cab_id}<br>Status: On Trip`);
                }
            }
            else {
                if (otherCabMarkers[cab_id]) {
                    map.removeLayer(otherCabMarkers[cab_id]);
                    delete otherCabMarkers[cab_id];
                }
            }
        }
    });
});