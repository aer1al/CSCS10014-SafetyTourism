// Initialize the map
const map = L.map('map').setView([0, 0], 2);

// Add the OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Layer groups for different markers
const layers = {
    disasters: L.layerGroup().addTo(map),
    storms: L.layerGroup().addTo(map),
    crowds: L.layerGroup().addTo(map),
    shelters: L.layerGroup().addTo(map),
    hospitals: L.layerGroup().addTo(map)
};

// Custom icons for different markers
const icons = {
    disaster: L.divIcon({
        className: 'custom-icon disaster',
        html: '<i class="fas fa-exclamation-triangle"></i>',
        iconSize: [30, 30]
    }),
    storm: L.divIcon({
        className: 'custom-icon storm',
        html: '<i class="fas fa-cloud-showers-heavy"></i>',
        iconSize: [30, 30]
    }),
    crowd: L.divIcon({
        className: 'custom-icon crowd',
        html: '<i class="fas fa-users"></i>',
        iconSize: [30, 30]
    }),
    shelter: L.divIcon({
        className: 'custom-icon shelter',
        html: '<i class="fas fa-house-damage"></i>',
        iconSize: [30, 30]
    }),
    hospital: L.divIcon({
        className: 'custom-icon hospital',
        html: '<i class="fas fa-hospital"></i>',
        iconSize: [30, 30]
    })
};

// Handle layer visibility toggles
document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const layerName = this.dataset.layer;
        const layer = layers[layerName];
        
        if (this.checked) {
            map.addLayer(layer);
        } else {
            map.removeLayer(layer);
        }
    });
});

// Function to fetch data from backend
async function fetchData(endpoint) {
    try {
        const response = await fetch(`/api/${endpoint}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Error fetching ${endpoint} data:`, error);
        return [];
    }
}

// Function to add markers to map
function addMarkers(data, layerName, icon) {
    layers[layerName].clearLayers();
    
    data.forEach(item => {
        const marker = L.marker([item.lat, item.lng], { icon: icons[icon] })
            .bindPopup(`
                <h3>${item.name}</h3>
                <p>${item.description}</p>
                ${item.details ? `<p>${item.details}</p>` : ''}
            `);
        
        layers[layerName].addLayer(marker);
    });
}

// Function to update map data
async function updateMapData() {
    // Fetch and update disasters
    const disasters = await fetchData('disaster');
    addMarkers(disasters, 'disasters', 'disaster');

    // Fetch and update weather/storms
    const storms = await fetchData('weather');
    addMarkers(storms, 'storms', 'storm');

    // Fetch and update crowd density
    const crowds = await fetchData('crowd');
    addMarkers(crowds, 'crowds', 'crowd');

    // Fetch and update shelters
    const shelters = await fetchData('shelter');
    addMarkers(shelters, 'shelters', 'shelter');

    // Fetch and update hospitals
    const hospitals = await fetchData('hospital');
    addMarkers(hospitals, 'hospitals', 'hospital');
}

// Get user's location
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const { latitude, longitude } = position.coords;
            map.setView([latitude, longitude], 13);
        }, error => {
            console.error('Error getting location:', error);
        });
    }
}

// Handle emergency call button
document.getElementById('callRescue').addEventListener('click', () => {
    window.location.href = 'tel:112'; // Emergency number
});

// Handle send GPS button
document.getElementById('sendGPS').addEventListener('click', async () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async position => {
            const { latitude, longitude } = position.coords;
            try {
                const response = await fetch('/api/emergency', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        lat: latitude,
                        lng: longitude
                    })
                });
                
                if (response.ok) {
                    alert('Your location has been sent to emergency services.');
                } else {
                    throw new Error('Failed to send location');
                }
            } catch (error) {
                console.error('Error sending location:', error);
                alert('Failed to send your location. Please try again.');
            }
        });
    }
});

// Initialize map with user location
getUserLocation();

// Update map data initially and every 5 minutes
updateMapData();
setInterval(updateMapData, 300000);