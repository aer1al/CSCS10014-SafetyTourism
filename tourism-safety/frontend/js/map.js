// 1. Khởi tạo bản đồ
const map = L.map('map').setView([10.7769, 106.7009], 14); 

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19, attribution: '© OpenStreetMap contributors'
}).addTo(map);

// ----- BIẾN TOÀN CỤC -----
let userLat = 0.0;
let userLon = 0.0;
let userMarker = null;
let currentRoutingControl = null; 
let routeControls = [];           
let routeBackups = []; // Lưu đường nét đứt dự phòng
let routeMarkers = []; // [MỚI] Lưu danh sách marker trạm dừng để xóa khi cần

// Layer groups
const layers = {
    disasters: L.layerGroup().addTo(map),
    storms: L.layerGroup().addTo(map),
    crowds: L.layerGroup().addTo(map),
    shelters: L.layerGroup().addTo(map),
    hospitals: L.layerGroup().addTo(map),
    routes: L.layerGroup().addTo(map) 
};

const markerColors = { disaster: '#ff4444', storm: '#5bc0de', crowd: '#ff8800', shelter: '#00C851', hospital: '#CC0000' };

// Xử lý Checkbox
document.querySelectorAll('.filter-item input[type="checkbox"]').forEach(checkbox => {
    checkbox.addEventListener('change', function() {
        const layerName = this.dataset.layer;
        
        if (layerName === 'routes') {
            if (this.checked) {
                loadMultiPointRoutes();
            } else {
                // Xóa sạch tất cả
                routeControls.forEach(c => map.removeControl(c));
                routeBackups.forEach(l => map.removeLayer(l));
                routeMarkers.forEach(m => map.removeLayer(m));
                routeControls = [];
                routeBackups = [];
                routeMarkers = [];
            }
            return;
        }

        if (!layers[layerName]) return;
        if (this.checked) map.addLayer(layers[layerName]);
        else map.removeLayer(layers[layerName]);
    });
});

async function fetchData(endpoint, lat, lon) {
    try {
        let url = `http://127.0.0.1:5000/api/${endpoint}`;
        if (lat && lon) url += `?lat=${lat}&lon=${lon}`;
        const response = await fetch(url); 
        if (!response.ok) throw new Error();
        return await response.json();
    } catch (e) { return []; }
}

// ==================================================================
// [CHIẾN THUẬT MỚI] VẼ NGAY LẬP TỨC (KHÔNG CHỜ SERVER)
// ==================================================================
async function loadMultiPointRoutes() {
    if (userLat === 0 && userLon === 0) return;

    console.log("Bắt đầu vẽ lộ trình...");
    
    const routes = await fetchData('custom-routes');
    if (!Array.isArray(routes) || routes.length === 0) return;

    // Dọn dẹp cũ (Quan trọng để không bị chồng lấn)
    routeControls.forEach(c => map.removeControl(c));
    routeBackups.forEach(l => map.removeLayer(l));
    routeMarkers.forEach(m => map.removeLayer(m));
    routeControls = [];
    routeBackups = [];
    routeMarkers = [];

    const routeCheckbox = document.querySelector('input[data-layer="routes"]');
    if (routeCheckbox && !routeCheckbox.checked) return;

    routes.forEach(route => {
        let backendPoints = route.points.map(point => L.latLng(point[0], point[1]));
        
        // Tạo danh sách điểm: [Vị trí của bạn] + [Các điểm backend bỏ điểm đầu]
        const waypoints = [L.latLng(userLat, userLon), ...backendPoints.slice(1)];

        // 1. VẼ NGAY LẬP TỨC đường nét đứt (Backup)
        // Để dù mạng chậm hay lỗi, người dùng vẫn thấy đường nối các điểm
        const backupLine = L.polyline(waypoints, {
            color: route.color || 'blue',
            weight: 4,
            opacity: 0.5,
            dashArray: '10, 10' 
        }).addTo(map);
        routeBackups.push(backupLine);

        // 2. VẼ NGAY LẬP TỨC các Marker (Trạm dừng)
        waypoints.forEach((wp, i) => {
            let label = '';
            let marker;

            if (i === 0) {
                label = '🏠 Vị trí của bạn';
                marker = L.marker(wp); // Marker to cho điểm đầu
            } else if (i === waypoints.length - 1) {
                label = '🏁 Kết thúc';
                marker = L.marker(wp); // Marker to cho điểm cuối
            } else {
                label = `Trạm dừng ${i}`;
                // Điểm giữa dùng chấm tròn màu vàng để dễ nhìn
                marker = L.circleMarker(wp, {
                    radius: 6, fillColor: 'yellow', color: '#000', weight: 1, fillOpacity: 1
                });
            }
            
            marker.addTo(map).bindPopup(`<b>${route.name}</b><br>${label}`);
            routeMarkers.push(marker); // Lưu vào danh sách để quản lý
        });

        // 3. Sau đó mới gọi Routing Machine để tính toán đường đẹp (Async)
        const routingControl = L.Routing.control({
            waypoints: waypoints,
            routeWhileDragging: false, 
            draggableWaypoints: false, 
            addWaypoints: false,       
            lineOptions: {
                styles: [{ color: route.color || 'blue', opacity: 0.8, weight: 6 }]
            },
            createMarker: function() { return null; }, // Không tạo marker mặc định nữa (vì đã tự vẽ ở trên)
            show: false, 
        });

        // Nếu vẽ thành công -> Xóa đường nét đứt (Backup), giữ lại đường đẹp
        routingControl.on('routesfound', function(e) {
            console.log(`✅ Đã vẽ xong đường chi tiết: ${route.name}`);
            map.removeLayer(backupLine); // Xóa đường backup cho đỡ rối
        });

        // Nếu lỗi -> Giữ nguyên đường nét đứt
        routingControl.on('routingerror', function(e) {
            console.warn(`⚠️ Lỗi Routing. Giữ nguyên đường thẳng dự phòng.`);
            backupLine.bindPopup(`<b>${route.name}</b><br>(Đường thẳng do lỗi mạng)`);
        });

        routingControl.addTo(map);
        routeControls.push(routingControl);
    });
}

// ----- [2] HÀM CHỈ ĐƯỜNG CÁ NHÂN -----
function calculateRoute(destLat, destLon) {
    if (userLat === 0 && userLon === 0) {
        alert("Chưa có vị trí của bạn."); return;
    }
    if (currentRoutingControl) map.removeControl(currentRoutingControl);

    // Vẽ đường backup ngay
    const backupPoly = L.polyline([L.latLng(userLat, userLon), L.latLng(destLat, destLon)], {
        color: 'blue', dashArray: '5, 10'
    }).addTo(map);

    currentRoutingControl = L.Routing.control({
        waypoints: [L.latLng(userLat, userLon), L.latLng(destLat, destLon)],
        routeWhileDragging: false,
        lineOptions: { styles: [{ color: '#0066ff', opacity: 0.8, weight: 6 }] },
        createMarker: function() { return null; },
        show: false, addWaypoints: false
    }).addTo(map);

    currentRoutingControl.on('routesfound', function() {
        map.removeLayer(backupPoly); // Xóa backup khi thành công
    });
}

function addMarkers(data, layerName, iconKey) {
    layers[layerName].clearLayers();
    const color = markerColors[iconKey] || '#808080';
    if (!Array.isArray(data)) return;

    data.forEach(item => {
        const marker = L.circleMarker([item.lat, item.lng], {
            radius: 8, fillColor: color, color: "#000", weight: 1, fillOpacity: 0.8
        });
        const div = document.createElement('div');
        div.innerHTML = `<div style="text-align:center"><h3 style="color:${color}">${item.name}</h3><p>${item.description}</p><button class="btn-route" style="background:#007bff;color:white;border:none;padding:5px;cursor:pointer">Chỉ đường</button></div>`;
        div.querySelector('.btn-route').onclick = () => { calculateRoute(item.lat, item.lng); map.closePopup(); };
        marker.bindPopup(div);
        layers[layerName].addLayer(marker);
    });
}

async function updateMapData(lat, lon) {
    const [d, s, c, sh, h] = await Promise.all([
        fetchData('disaster', lat, lon), fetchData('weather', lat, lon),
        fetchData('crowd', lat, lon), fetchData('shelter', lat, lon), fetchData('hospital', lat, lon)
    ]);
    addMarkers(d, 'disasters', 'disaster'); addMarkers(s, 'storms', 'storm');
    addMarkers(c, 'crowds', 'crowd'); addMarkers(sh, 'shelters', 'shelter'); addMarkers(h, 'hospitals', 'hospital');
}

// ----- [4] CẬP NHẬT VỊ TRÍ THỦ CÔNG -----
function updateUserLocationManual(lat, lon) {
    userLat = lat; userLon = lon;
    if (userMarker) map.removeLayer(userMarker);

    userMarker = L.marker([userLat, userLon], {draggable: true}).addTo(map);
    userMarker.bindPopup("<b>Bạn đang ở đây</b>").openPopup();

    userMarker.on('dragend', function(e) {
        const pos = userMarker.getLatLng();
        userLat = pos.lat; userLon = pos.lng;
        
        updateMapData(userLat, userLon);
        loadMultiPointRoutes(); // Vẽ lại lộ trình từ vị trí mới

        if (currentRoutingControl) {
            const waypoints = currentRoutingControl.getWaypoints();
            calculateRoute(waypoints[waypoints.length - 1].latLng.lat, waypoints[waypoints.length - 1].latLng.lng);
        }
    });

    map.setView([userLat, userLon], 14);
    updateMapData(userLat, userLon);
    
    // Gọi vẽ đường ngay lần đầu có vị trí
    loadMultiPointRoutes();
}

// ----- [5] LẤY GPS -----
function getUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => updateUserLocationManual(pos.coords.latitude, pos.coords.longitude), 
            (err) => {
                console.warn('GPS Error. Load default.');
                updateUserLocationManual(10.7769, 106.7009); 
                alert("Không tìm thấy vị trí. Đang hiển thị tại HCM.\nHãy kéo ghim về đúng vị trí của bạn.");
            },
            { enableHighAccuracy: true, timeout: 5000 }
        );
    } else {
        updateUserLocationManual(10.7769, 106.7009);
    }
}

document.getElementById('callRescue').onclick = () => window.location.href = 'tel:112';
document.getElementById('sendGPS').onclick = async () => {
    if(userLat===0) return alert("Chưa có GPS");
    try { await fetch('http://127.0.0.1:5000/api/emergency', {
        method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({lat:userLat, lng:userLon})
    }); alert("Đã gửi!"); } catch(e){ alert("Lỗi gửi!"); }
};

// RUN
getUserLocation();
