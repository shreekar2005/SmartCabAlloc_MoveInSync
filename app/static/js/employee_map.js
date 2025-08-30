document.addEventListener('DOMContentLoaded', (event) => {
    const map = L.map('map').setView([26.4715, 73.1134], 15);
    const statusMessage = document.getElementById('status-message');
    const requestTripBtn = document.getElementById('request-trip-btn');
    
    let myLocationMarker = null;
    let allocatedCabMarker = null;
    let tripLine = null;
    let myTripId = null;
    let myCabId = null;

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
    // Draw my location
    if (typeof userLocation !== 'undefined' && userLocation.lat && userLocation.lon) {
        myLocationMarker = L.marker([userLocation.lat, userLocation.lon], { icon: icons.myLocation })
            .addTo(map)
            .bindPopup('My Location').openPopup();
        map.setView([userLocation.lat, userLocation.lon], 15);
    }

    // Draw other cabs on trip
    if (typeof onTripCabs !== 'undefined') {
        onTripCabs.forEach(cab => {
            L.marker([cab.current_lat, cab.current_lon], { icon: icons.onTripOther })
                .addTo(map)
                .bindPopup(`Cab ID: ${cab.id}<br>Status: On Trip`);
        });
    }

    // Draw my allocated cab if any
    if (typeof allocatedCab !== 'undefined' && allocatedCab) {
        myCabId = allocatedCab.id;
        myTripId = allocatedCab.trip_id; // Assuming trip_id is passed with allocatedCab
        allocatedCabMarker = L.marker([allocatedCab.current_lat, allocatedCab.current_lon], { icon: icons.myCab })
            .addTo(map)
            .bindPopup(`My Cab<br>ID: ${allocatedCab.id}`);
        tripLine = L.polyline([myLocationMarker.getLatLng(), allocatedCabMarker.getLatLng()], { color: '#FF0000' }).addTo(map);
        statusMessage.textContent = `Cab ${myCabId} is on the way!`;
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
            const response = await fetch('/employee/request-trip', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ lat: myLocationMarker.getLatLng().lat, lon: myLocationMarker.getLatLng().lng })
            });
            const data = await response.json();
            if (response.ok) {
                myTripId = data.trip_id;
                statusMessage.textContent = `Trip Requested (ID: ${myTripId}). Waiting for allocation.`;
            } else {
                statusMessage.textContent = `Error: ${data.message}`;
                requestTripBtn.disabled = false;
            }
        } catch (error) {
            statusMessage.textContent = 'An unexpected error occurred.';
            console.error('Request failed:', error);
            requestTripBtn.disabled = false;
        }
    });

    // --- WebSocket Event Handlers ---
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', () => console.log('Connected to WebSocket for employee dashboard.'));

    socket.on('trip_allocated', (data) => {
        if (data.employee_id === userPublicId) { // Use userPublicId for comparison
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
        }
    });

    socket.on('location_update', (data) => {
        if (allocatedCabMarker && data.cab_id === myCabId) {
            const cabLatLng = [data.lat, data.lon];
            allocatedCabMarker.setLatLng(cabLatLng);
            if (tripLine) {
                tripLine.setLatLngs([myLocationMarker.getLatLng(), cabLatLng]);
            }
        }
    });
});