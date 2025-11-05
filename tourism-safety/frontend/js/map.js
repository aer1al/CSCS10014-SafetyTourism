// Initialize the map
const map = L.map('map').setView([0, 0], 2);

// Add the OpenStreetMap tiles
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// ----- THÊM 2 BIẾN NÀY ĐỂ LƯU VỊ TRÍ -----
let userLat = 0.0;
let userLon = 0.0;

// Layer groups for different markers
const layers = {
    disasters: L.layerGroup().addTo(map),
    storms: L.layerGroup().addTo(map),
    crowds: L.layerGroup().addTo(map),
    shelters: L.layerGroup().addTo(map),
    hospitals: L.layerGroup().addTo(map)
};

// ----- BẢNG MÀU CHO CÁC CHẤM TRÒN (ĐỂ GIỐNG LEGEND) -----
const markerColors = {
    disaster: '#ff4444',
    storm: '#5bc0de',
    crowd: '#ff8800',
    shelter: '#00C851',
    hospital: '#CC0000'
};

// Handle layer visibility toggles (Giữ nguyên)
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

// ----- SỬA HÀM NÀY ĐỂ GỬI lat/lon LÊN BACKEND -----
async function fetchData(endpoint, lat, lon) {
    try {
        // Thêm http://127.0.0.1:5500 vào
        const response = await fetch(`http://127.0.0.1:5000/api/${endpoint}?lat=${lat}&lon=${lon}`); 
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error(`Error fetching ${endpoint} data:`, error);
        return []; 
    }
}

// ----- HÀM NÀY BÂY GIỜ RẤT SẠCH (Vì backend đã dọn dẹp) -----
function addMarkers(data, layerName, iconKey) {
    layers[layerName].clearLayers();
    
    const color = markerColors[iconKey] || '#808080'; // Lấy màu

    // Backend ĐÃ ĐẢM BẢO data là một mảng
    if (!Array.isArray(data)) {
         console.error(`Lỗi: Dữ liệu cho '${layerName}' không phải là mảng:`, data);
         return;
    }

    data.forEach(item => {
        // Backend ĐÃ ĐẢM BẢO key là 'lat' và 'lng'
        if (item.lat === undefined || item.lng === undefined) {
            console.warn("Bỏ qua item vì thiếu lat/lng:", item);
            return;
        }

        // Tạo Chấm tròn (CircleMarker)
        const marker = L.circleMarker([item.lat, item.lng], {
            radius: 8,
            fillColor: color,
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        })
        .bindPopup(`
            <h3>${item.name}</h3>
            <p>${item.description}</p>
            ${item.details ? `<p>${item.details}</p>` : ''}
        `);
        
        layers[layerName].addLayer(marker);
    });
}

// ----- SỬA HÀM NÀY ĐỂ TRUYỀN lat/lon VÀO -----
async function updateMapData(lat, lon) {
    // Fetch and update disasters
    const disasters = await fetchData('disaster', lat, lon);
    addMarkers(disasters, 'disasters', 'disaster');

    // Fetch and update weather/storms
    const storms = await fetchData('weather', lat, lon);
    addMarkers(storms, 'storms', 'storm');

    // Fetch and update crowd density
    const crowds = await fetchData('crowd', lat, lon);
    addMarkers(crowds, 'crowds', 'crowd');

    // Fetch and update shelters
    const shelters = await fetchData('shelter', lat, lon);
    addMarkers(shelters, 'shelters', 'shelter');

    // Fetch and update hospitals
    const hospitals = await fetchData('hospital', lat, lon);
    addMarkers(hospitals, 'hospitals', 'hospital');
}

// ----- SỬA HÀM NÀY ĐỂ GỌI updateMapData SAU KHI CÓ VỊ TRÍ -----
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(position => {
            const { latitude, longitude } = position.coords;
            
            // Lưu vị trí vào biến toàn cục
            userLat = latitude;
            userLon = longitude; // Lưu ý: ở đây JS dùng 'longitude'

            map.setView([userLat, userLon], 13);

            // GỌI HÀM UPDATE VỚI TỌA ĐỘ MỚI
            updateMapData(userLat, userLon); // Gửi userLon (backend nhận là 'lon')
            // Cập nhật mỗi 5 phút
            setInterval(() => updateMapData(userLat, userLon), 300000);

        }, error => {
            console.error('Error getting location:', error);
            // Nếu lỗi, vẫn gọi update (backend sẽ dùng tọa độ 0,0 hoặc mặc định)
            updateMapData(userLat, userLon); 
        });
    } else {
         // Nếu trình duyệt không hỗ trợ
        updateMapData(userLat, userLon);
    }
}

// Giữ nguyên code 2 nút 'callRescue' và 'sendGPS'
document.getElementById('callRescue').addEventListener('click', () => {
    window.location.href = 'tel:112';
});

document.getElementById('sendGPS').addEventListener('click', async () => {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async position => {
            const { latitude, longitude } = position.coords;
            try {
                // SỬA Ở ĐÂY: Thêm 'http://127.0.0.1:5000'
                const response = await fetch('http://127.0.0.1:5000/api/emergency', {
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

// ----- XÓA 2 DÒNG NÀY ĐI -----
// (Vì chúng ta đã chuyển nó vào trong hàm getUserLocation)
// updateMapData();
// setInterval(updateMapData, 300000);