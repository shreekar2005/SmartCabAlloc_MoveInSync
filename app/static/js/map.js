document.addEventListener('DOMContentLoaded', (event) => {
    // Initialize the map and set its view to New York City
    const map = L.map('map').setView([40.7128, -74.0060], 12);

    // Add an OpenStreetMap tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // This object will store cab markers, with cab_id as the key
    const cabMarkers = {};

    // Connect to the Flask-SocketIO server
    const socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', () => {
        console.log('Connected to WebSocket server!');
    });

    // Listen for 'location_update' events from the server
    socket.on('location_update', (data) => {
        console.log('Received location update:', data);
        const { cab_id, lat, lon, status } = data;

        const popupContent = `<b>Cab ID:</b> ${cab_id}<br><b>Status:</b> ${status}`;

        if (cabMarkers[cab_id]) {
            // If marker already exists, update its position and popup
            cabMarkers[cab_id].setLatLng([lat, lon]).setPopupContent(popupContent);
        } else {
            // If marker doesn't exist, create a new one and add it to the map
            cabMarkers[cab_id] = L.marker([lat, lon])
               .addTo(map)
               .bindPopup(popupContent);
        }
    });
});