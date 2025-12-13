let routeLayers = [];
let riskLayers = L.layerGroup(); // Layer chứa các vòng tròn rủi ro (Minh chứng)
let startMarker = null;
let endMarker = null;
const API_URL = "http://127.0.0.1:5000/api/find-routes";

// Đảm bảo map đã load xong mới add layer
if (typeof map !== 'undefined') {
    riskLayers.addTo(map);
} else {
    window.addEventListener('load', () => {
        if (typeof map !== 'undefined') riskLayers.addTo(map);
    });
}

document.getElementById("searchBtn").addEventListener("click", async () => {
  const startInput = document.getElementById("startPoint");
  const endInput = document.getElementById("endPoint");
  const statusArea = document.getElementById("status-area");
  
  const startLat = startInput.dataset.lat; 
  const startLon = startInput.dataset.lon;
  const endLat = endInput.dataset.lat; 
  const endLon = endInput.dataset.lon;

  if (!startLat || !endLat) { 
      alert("Vui lòng chọn địa điểm!"); 
      return; 
  }

  statusArea.innerHTML = `<div class="status-box loading">⏳ Đang phân tích rủi ro & tìm đường...</div>`;

  try {
    // 1. CHUẨN BỊ PAYLOAD
    const modeSelect = document.getElementById("vehicleMode").value;
    const prefWeather = parseFloat(document.getElementById("pref-weather").value || 1.0);
    const prefCrowd = parseFloat(document.getElementById("pref-crowd").value || 1.0);

    const payload = {
      start: [parseFloat(startLat), parseFloat(startLon)],
      end: [parseFloat(endLat), parseFloat(endLon)],
      mode: modeSelect,
      preferences: {
          traffic: 1.0,
          weather: prefWeather,
          crowd: prefCrowd, 
          disaster: 1.0
      }
    };

    // 2. GỌI API
    const response = await fetch(API_URL, {
      method: "POST", 
      headers: { "Content-Type": "application/json" }, 
      body: JSON.stringify(payload)
    });
    const data = await response.json();

    if (data.status === "error") throw new Error(data.message);

    window.currentRouteData = data; 

    // 3. XỬ LÝ BẢN ĐỒ
    clearMapLayers(); // Xóa đường cũ & rủi ro cũ
    drawMarkers([startLat, startLon], [endLat, endLon]);

    // A. VẼ MINH CHỨNG RỦI RO (QUAN TRỌNG)
    // Dữ liệu này đã được Backend cắt (clip) theo BBox -> Không bị full graph
    if (data.map_data) {
        drawRiskEvidence(data.map_data);
    }

    // B. VẼ ĐƯỜNG PHỤ
    if (data.alternatives && data.alternatives.length > 0) {
        data.alternatives.forEach((altRoute, index) => {
            drawSingleRoute(altRoute, "alternative", `Đường phụ ${index + 1}`);
        });
    }

    // C. VẼ ĐƯỜNG CHÍNH
    // Clone object để tránh tham chiếu vòng
    const mainRouteObj = { ...data, geometry: data.geometry }; 
    drawSingleRoute(mainRouteObj, "main", data.summary.description);

    // Zoom vừa vặn với tất cả các đường
    if (routeLayers.length > 0) {
        const group = new L.featureGroup(routeLayers);
        map.fitBounds(group.getBounds(), { padding: [50, 50] });
    }

    // Hiển thị thông tin
    displayRouteInfo(data, statusArea, "CHÍNH (Tốt nhất)");

  } catch (error) {
    console.error(error);
    statusArea.innerHTML = `<div class="status-box error">❌ ${error.message}</div>`;
  }
});

// --- HÀM VẼ MINH CHỨNG RỦI RO (Weather, Disaster, Crowd) ---
function drawRiskEvidence(mapData) {
    riskLayers.clearLayers(); // Xóa rủi ro cũ

    // 1. VẼ THIÊN TAI (Bão/Lũ) - Màu Đỏ
    if (mapData.disasters) {
        mapData.disasters.forEach(d => {
            // Vòng tròn cảnh báo đỏ
            L.circle([d.lat, d.lng], {
                color: '#e74c3c', fillColor: '#e74c3c', fillOpacity: 0.2,
                radius: (d.radius || 5) * 1000, weight: 1,
                type: 'disaster' // Gán type để nhận diện sau này
            }).addTo(riskLayers);

            // Icon ngọn lửa/bão
            const icon = L.divIcon({
                className: 'custom-div-icon',
                html: '<div style="font-size:20px; text-shadow: 0 0 5px white;">🌋</div>',
                iconSize: [25, 25], iconAnchor: [12, 12]
            });
            L.marker([d.lat, d.lng], { icon: icon, type: 'disaster' }) // Gán type để nhận diện sau này
             .bindPopup(`<b style="color:red">${d.name}</b><br>Bán kính: ${d.radius}km`).addTo(riskLayers);
        });
    }

    // 2. VẼ THỜI TIẾT (Mưa/Gió) - Màu Xanh/Xám
    // Đây là cái bạn thiếu: Vẽ trực tiếp weather data lên map
    if (mapData.weather) {
        mapData.weather.forEach(w => {
            // Chỉ vẽ nếu là Mưa hoặc Gió to
            if (w.condition === 'Clear' && w.wind_speed < 10) return;

            let color = '#3498db'; // Mưa thường: Xanh dương
            let emoji = '🌧️';
            
            if (w.condition === 'Thunderstorm' || w.wind_speed > 15) {
                color = '#555'; // Bão/Gió to: Xám đen
                emoji = '⛈️';
            } else if (w.wind_speed > 10) {
                emoji = '💨';
            }

            // Vùng ảnh hưởng
            L.circle([w.lat, w.lng], {
                color: color, fillColor: color, fillOpacity: 0.25,
                radius: (w.radius || 2) * 1000, weight: 0,
                type: 'weather' // Gán type để nhận diện sau này
            }).addTo(riskLayers);
            
            // Marker biểu tượng
            L.marker([w.lat, w.lng], { 
                icon: L.divIcon({
                    html: `<div style="font-size:18px;">${emoji}</div>`, 
                    className: '', 
                    iconSize:[20,20],
                    iconAnchor: [10, 10]
                }) 
                , type: 'weather' // Gán type để nhận diện sau này
            }).bindPopup(`<b>${w.condition}</b><br>Gió: ${w.wind_speed} m/s`).addTo(riskLayers);
        });
    }

    // 3. VẼ ĐÁM ĐÔNG (Crowd) - Chấm Vàng
    if (mapData.crowd) {
        mapData.crowd.forEach(c => {
            L.circleMarker([c.lat, c.lng], {
                radius: 5,
                color: '#f39c12', fillColor: '#f1c40f', fillOpacity: 0.9, weight: 1,
                type: 'crowd' // Gán type để nhận diện sau này
            }).bindPopup(`<b>👥 ${c.name}</b>`).addTo(riskLayers);
        });
    }
}

function clearMapLayers() {
    // 1. Xóa các đường đi (Routes)
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
    
    // 2. Xóa lớp rủi ro (Risk Circles)
    riskLayers.clearLayers();
    
    // 3. Xóa Marker Start/End (QUAN TRỌNG)
    if (startMarker) {
        map.removeLayer(startMarker);
        startMarker = null; // Gán null để reset
    }
    if (endMarker) {
        map.removeLayer(endMarker);
        endMarker = null; // Gán null để reset
    }
    
    // 4. Đóng tất cả popup đang mở
    map.closePopup();
}

function drawMarkers(start, end) {
    const startIcon = L.divIcon({className: "custom-div-icon", html: `<div class="start-marker">🚀</div>`, iconSize: [36, 36], iconAnchor: [18, 42], popupAnchor: [0, -40]});
    startMarker = L.marker(start, {icon: startIcon}).addTo(map).bindPopup("<b>Điểm đi</b>");

    const endIcon = L.divIcon({className: "custom-div-icon", html: `<div class="end-marker">🏁</div>`, iconSize: [36, 36], iconAnchor: [18, 42], popupAnchor: [0, -40]});
    endMarker = L.marker(end, {icon: endIcon}).addTo(map).bindPopup("<b>Điểm đến</b>");
}

function drawSingleRoute(routeData, type, title) {
    const isMain = type === "main";
    const color = isMain ? "#0061ff" : "#4aa3ff"; 
    const opacity = isMain ? 1.0 : 0.6;       
    const weight = isMain ? 7 : 5;            
    const zIndex = isMain ? 1000 : 500;       

    const polyline = L.polyline(routeData.geometry, {
        color: color, weight: weight, opacity: opacity,
        lineCap: 'round', lineJoin: 'round', zIndexOffset: zIndex
    }).addTo(map);

    polyline.bindTooltip(`<b>${title}</b><br>Bấm để xem chi tiết`, { sticky: true });

    polyline.on('mouseover', function() { 
        this.setStyle({ weight: 9, opacity: 1.0, color: '#00c6ff' }); 
        this.bringToFront();
    });
    polyline.on('mouseout', function() { 
        this.setStyle({ weight: weight, opacity: opacity, color: color }); 
        if (!isMain) this.bringToBack();
    });

    polyline.on('click', function() {
        const statusArea = document.getElementById("status-area");
        displayRouteInfo(routeData, statusArea, title);
        routeLayers.forEach(l => l.setStyle({ opacity: 0.4 })); 
        this.setStyle({ opacity: 1.0, color: '#0061ff' });      
    });

    routeLayers.push(polyline);
}

function displayRouteInfo(data, container, routeLabel) {
  const summary = data.summary || {};
  const risks = data.risk_summary || {};
  
  let badgeClass = "safe-badge"; let icon = "✅";
  if (summary.safety_color === "red") { badgeClass = "danger-badge"; icon = "⛔"; }
  else if (summary.safety_color === "yellow") { badgeClass = "warning-badge"; icon = "⚠️"; }

  const getBadgeInfo = (level) => {
      if (level === "High") return { class: "bad", text: "Cao" };
      if (level === "Medium") return { class: "medium", text: "Vừa" };
      return { class: "good", text: "Thấp" };
  };
  const trafficInfo = getBadgeInfo(risks.traffic_level);
  const crowdInfo = getBadgeInfo(risks.crowd_level);

  let proofHtml = summary.avoidance_proof ? 
      `<div style="margin-top:8px; padding:6px; background:#e8f5e9; border-radius:6px; font-size:11px; color:#2e7d32;">
        🛡️ ${summary.avoidance_proof}
       </div>` : "";

  container.innerHTML = `
    <div class="result-card">
        <div style="margin-bottom:10px; font-weight:bold; color:#00509d; border-bottom:1px solid #eee; padding-bottom:5px;">
            📍 Đang xem: ${routeLabel || "Lộ trình"}
        </div>
        <div class="route-stats">
            <div class="stat"><span class="value">${data.distance_km}</span><span class="label">KM</span></div>
            <div class="divider-vertical"></div>
            <div class="stat"><span class="value">${data.duration_min}</span><span class="label">PHÚT</span></div>
        </div>
        <div class="risk-section">
            <div class="${badgeClass}" style="padding:10px; border-radius:8px;">
                <div style="font-size:14px; margin-bottom:4px;">${icon} <strong>${summary.safety_label}</strong></div>
                <div style="font-size:12px; opacity:0.9;">${summary.description}</div>
            </div>
            ${proofHtml}
        </div>
        <div class="status-grid">
            <div class="status-item"><span class="status-label">🚦 Kẹt xe</span><span class="status-badge ${trafficInfo.class}">${trafficInfo.text}</span></div>
            <div class="status-item"><span class="status-label">👥 Đám đông</span><span class="status-badge ${crowdInfo.class}">${crowdInfo.text}</span></div>
        </div>
    </div>
  `;
}

// --- LOGIC BẬT TẮT LAYER (Dán vào cuối find_route.js) ---

// Lắng nghe sự kiện thay đổi của 3 checkbox
['chk-weather', 'chk-disaster', 'chk-crowd'].forEach(id => {
    const checkbox = document.getElementById(id);
    if (checkbox) {
        checkbox.addEventListener('change', updateLayerVisibility);
    }
});

function updateLayerVisibility() {
    // Lấy trạng thái của 3 nút (true/false)
    const showWeather = document.getElementById('chk-weather').checked;
    const showDisaster = document.getElementById('chk-disaster').checked;
    const showCrowd = document.getElementById('chk-crowd').checked;

    riskLayers.eachLayer(layer => {
        // Lấy cái thẻ bài "type" mình vừa gắn ở bước trên
        const type = layer.options.type;

        // Logic ẩn/hiện cực đơn giản
        if (type === 'weather') {
            if (showWeather) map.addLayer(layer); else map.removeLayer(layer);
        } 
        else if (type === 'disaster') {
            if (showDisaster) map.addLayer(layer); else map.removeLayer(layer);
        } 
        else if (type === 'crowd') {
            if (showCrowd) map.addLayer(layer); else map.removeLayer(layer);
        }
    });
}

// --- XỬ LÝ NÚT DEMO MODE ---
const demoToggle = document.getElementById('demoToggle');

if (demoToggle) {
    // 1. Mặc định tắt (hoặc ông có thể gọi API để lấy trạng thái hiện tại nếu muốn xịn hơn)
    demoToggle.checked = false; 

    // 2. Lắng nghe sự kiện gạt nút
    demoToggle.addEventListener('change', async (e) => {
        const isDemo = e.target.checked;
        const statusArea = document.getElementById("status-area");
        
        try {
            // Gọi API báo cho Backend biết
            const res = await fetch('http://127.0.0.1:5000/api/toggle-demo', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ demo: isDemo })
            });
            const data = await res.json();
            
            // Thông báo nhỏ
            if(data.status === 'success') {
                console.log(data.message);
                // Nếu đang bật Demo, hiện cảnh báo cho user biết
                if(statusArea) {
                    statusArea.innerHTML = isDemo 
                        ? `<div class="status-box warning" style="background:#fff3e0; color:#ef6c00;">⚠️ Đang chạy chế độ DEMO (Dữ liệu giả)</div>`
                        : `<div class="status-box success" style="background:#e8f5e9; color:#2e7d32;">✅ Đang chạy REALTIME (Dữ liệu thật)</div>`;
                }
            }
        } catch (err) {
            console.error("Lỗi chuyển chế độ:", err);
            alert("Không kết nối được với Server để chuyển chế độ!");
            // Trả nút về vị trí cũ nếu lỗi
            e.target.checked = !isDemo;
        }
    });
}