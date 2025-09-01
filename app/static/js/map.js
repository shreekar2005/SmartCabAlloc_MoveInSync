document.addEventListener('DOMContentLoaded', (event) => {
    const map = L.map('map').setView([26.2389, 73.0243], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    const cabMarkers = {};
    const pendingTripsList = document.getElementById('trip-requests-ul');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const createIcon = (color) => L.icon({
        iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    const icons = {
        available: createIcon('green'),
        on_trip: createIcon('yellow')
    };

    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function (map) {
        const div = L.DomUtil.create('div', 'info legend');
        const items = {
            'Available Cab': 'green',
            'Cab on Trip': 'yellow'
        };
        let labels = '<strong>Legend</strong><br>';
        for (const item in items) {
            labels += `<i style="background-image: url(https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${items[item]}.png); background-size: contain; display: inline-block; width: 12px; height: 20px; vertical-align: middle;"></i> ${item}<br>`;
        }
        div.innerHTML = labels;
        return div;
    };
    legend.addTo(map);

    function addPendingTripToList(trip) {
        const listItem = document.createElement('li');
        listItem.id = `trip-${trip.id}`;
        listItem.innerHTML = `
            <strong>Trip ID:</strong> ${trip.id}<br>
            Employee ID: ${trip.employee_id}<br>
            Location: (${trip.start_lat.toFixed(4)}, ${trip.start_lon.toFixed(4)})<br>
            <button data-trip-id="${trip.id}" class="allocate-btn">Allocate Cab</button>
            <hr>
        `;
        pendingTripsList.appendChild(listItem);

        // Add click listener to the allocate button
        listItem.querySelector('.allocate-btn').addEventListener('click', async (e) => {
            const tripId = e.target.dataset.tripId;
            e.target.disabled = true;
            e.target.textContent = 'Allocating...';

            try {
                // Get the CSRF token
                const csrfToken = getCookie('csrf_access_token');

                const response = await fetch(`/admin/trips/${tripId}/allocate`, {
                    method: 'POST',
                    // Add the required header for CSRF protection
                    headers: {
                        'X-CSRF-Token': csrfToken
                    }
                });
                
                const data = await response.json();
                if (!response.ok) {
                    alert(`Allocation failed: ${data.message || data.msg}`);
                    e.target.disabled = false;
                    e.target.textContent = 'Allocate Cab';
                }
            } catch (error) {
                alert('An error occurred during allocation.');
                console.error(error);
                e.target.disabled = false;
                e.target.textContent = 'Allocate Cab';
            }
        });
    }

    if (typeof allCabs !== 'undefined') {
        allCabs.forEach(cab => {
            const icon = cab.status === 'available' ? icons.available : icons.on_trip;
            cabMarkers[cab.id] = L.marker([cab.current_lat, cab.current_lon], { icon: icon })
                .addTo(map)
                .bindPopup(`<b>Cab ID:</b> ${cab.id}<br><b>Status:</b> ${cab.status}`);
        });
    }

    if (typeof pendingTrips !== 'undefined') {
        pendingTrips.forEach(trip => {
            addPendingTripToList(trip);
        });
    }

    // WebSocket for Real-Time Updates
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', () => {
        console.log('Connected to WebSocket server!');
        socket.emit('join_admin_room');
    });

    socket.on('location_update', (data) => {
        const { cab_id, lat, lon, status } = data;
        const icon = status === 'available' ? icons.available : icons.on_trip;
        if (cabMarkers[cab_id]) {
            cabMarkers[cab_id].setLatLng([lat, lon]).setIcon(icon);
            cabMarkers[cab_id].getPopup().setContent(`<b>Cab ID:</b> ${cab_id}<br><b>Status:</b> ${status}`);
        } else {
            cabMarkers[cab_id] = L.marker([lat, lon], { icon: icon })
                .addTo(map)
                .bindPopup(`<b>Cab ID:</b> ${cab_id}<br><b>Status:</b> ${status}`);
        }
    });

    socket.on('new_trip_request', (data) => {
        console.log('New trip request received:', data);
        addPendingTripToList(data);
    });

    socket.on('trip_allocated', (data) => {
        console.log('Trip allocated event received:', data);
        const { trip_id, cab_id } = data;

        const listItem = document.getElementById(`trip-${trip_id}`);
        if (listItem) {
            listItem.remove();
        }

        if (cabMarkers[cab_id]) {
            cabMarkers[cab_id].setIcon(icons.on_trip);
            cabMarkers[cab_id].getPopup().setContent(`<b>Cab ID:</b> ${cab_id}<br><b>Status:</b> On Trip (Allocated)`);
        }
    });
});