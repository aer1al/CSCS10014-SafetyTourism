// js/find_route.js

let routeLayers = [];
let startMarker = null;
let endMarker = null;
const API_URL = "http://127.0.0.1:5000/api/find-routes";

document.getElementById("searchBtn").addEventListener("click", async () => {
  const startInput = document.getElementById("startPoint");
  const endInput = document.getElementById("endPoint");
  const statusArea = document.getElementById("status-area");
  const startLat = startInput.dataset.lat; const startLon = startInput.dataset.lon;
  const endLat = endInput.dataset.lat; const endLon = endInput.dataset.lon;

  if (!startLat || !endLat) { alert("Vui lòng chọn địa điểm!"); return; }

  statusArea.innerHTML = `<div class="status-box loading">⏳ Đang tìm 3 lộ trình tối ưu...</div>`;

  try {
    // 1. LẤY DỮ LIỆU TỪ FORM MỚI
    const modeSelect = document.getElementById("vehicleMode").value;
    const prefWeather = parseFloat(document.getElementById("pref-weather").value);
    const prefCrowd = parseFloat(document.getElementById("pref-crowd").value);

    const payload = {
      start: [parseFloat(startLat), parseFloat(startLon)],
      end: [parseFloat(endLat), parseFloat(endLon)],
      mode: modeSelect,
      preferences: {
          traffic: 1.0,   // Mặc định luôn là 1 (như bạn yêu cầu)
          weather: prefWeather,
          crowd: prefCrowd, 
          disaster: 1.0   // Thiên tai luôn né tối đa
      }
    };

    const response = await fetch(API_URL, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
    });
    const data = await response.json();

    if (data.status === "error") throw new Error(data.message);

    window.currentRouteData = data; // Lưu dữ liệu chính

    // --- XỬ LÝ BẢN ĐỒ ---
    clearMapLayers();
    drawMarkers([startLat, startLon], [endLat, endLon]);

    // A. VẼ ĐƯỜNG PHỤ (ALTERNATIVES)
    if (data.alternatives && data.alternatives.length > 0) {
        data.alternatives.forEach((altRoute, index) => {
            // Truyền cả object altRoute vào để lấy thông số khi click
            drawSingleRoute(altRoute, "alternative", `Đường phụ ${index + 1}`);
        });
    }

    // B. VẼ ĐƯỜNG CHÍNH (MAIN)
    // Gộp data chính vào format giống alternative để hàm vẽ xử lý đồng nhất
    const mainRouteObj = { ...data, geometry: data.geometry }; 
    drawSingleRoute(mainRouteObj, "main", data.summary.description);

    // Zoom
    if (routeLayers.length > 0) {
        const group = new L.featureGroup(routeLayers);
        map.fitBounds(group.getBounds(), { padding: [50, 50] });
    }

    // Update Layers
    if (data.map_data && typeof drawLayers === "function") drawLayers(data.map_data);

    // Hiển thị thông tin đường CHÍNH mặc định
    displayRouteInfo(data, statusArea, "CHÍNH (Tốt nhất)");

  } catch (error) {
    console.error(error);
    statusArea.innerHTML = `<div class="status-box error">❌ ${error.message}</div>`;
  }
});

// --- HÀM VẼ 1 ĐƯỜNG (CÓ CLICK EVENT) ---
function drawSingleRoute(routeData, type, title) {
    const isMain = type === "main";
    
    // --- STYLE ĐƯỜNG ---
    // Đường chính: Xanh đậm (#0061ff), đậm, nổi
    // Đường phụ: Xanh nhạt (#4aa3ff), mờ hơn, nhỏ hơn, KHÔNG NÉT ĐỨT
    const color = isMain ? "#0061ff" : "#4aa3ff"; 
    const opacity = isMain ? 1.0 : 0.6;       // Đường phụ mờ đi
    const weight = isMain ? 7 : 5;            // Đường phụ nhỏ hơn
    const zIndex = isMain ? 1000 : 500;       // Đường chính nằm trên

    const polyline = L.polyline(routeData.geometry, {
        color: color,
        weight: weight,
        opacity: opacity,
        lineCap: 'round',
        lineJoin: 'round',
        zIndexOffset: zIndex
    }).addTo(map);

    // --- SỰ KIỆN TƯƠNG TÁC ---
    
    // 1. Popup khi hover
    polyline.bindTooltip(`<b>${title}</b><br>Bấm để xem chi tiết`, { sticky: true });

    // 2. Hiệu ứng Hover (Làm nổi đường khi chuột rà vào)
    polyline.on('mouseover', function() { 
        this.setStyle({ weight: 9, opacity: 1.0, color: '#00c6ff' }); 
        this.bringToFront();
    });
    polyline.on('mouseout', function() { 
        this.setStyle({ weight: weight, opacity: opacity, color: color }); 
        if (!isMain) this.bringToBack();
    });

    // 3. CLICK -> HIỆN THÔNG SỐ RA SIDEBAR (QUAN TRỌNG)
    polyline.on('click', function() {
        const statusArea = document.getElementById("status-area");
        // Gọi hàm hiển thị thông tin của CHÍNH ĐƯỜNG NÀY
        displayRouteInfo(routeData, statusArea, title);
        
        // Highlight đường đang chọn (đổi màu tạm thời)
        routeLayers.forEach(l => l.setStyle({ opacity: 0.4 })); // Làm mờ tất cả
        this.setStyle({ opacity: 1.0, color: '#0061ff' });      // Làm rõ đường chọn
    });

    routeLayers.push(polyline);
}

// --- HÀM HIỂN THỊ INFO (Cập nhật để hiện tên đường đang chọn) ---
function displayRouteInfo(data, container, routeLabel) {
  const summary = data.summary || {};
  const risks = data.risk_summary || {};
  
  // Logic màu sắc Badge
  let badgeClass = "safe-badge"; let icon = "✅";
  if (summary.safety_color === "red") { badgeClass = "danger-badge"; icon = "⛔"; }
  else if (summary.safety_color === "yellow") { badgeClass = "warning-badge"; icon = "⚠️"; }

  // Badge nhỏ
  const getBadgeInfo = (level, type) => {
      if (level === "High") return { class: "bad", text: "Cao" };
      if (level === "Medium") return { class: "medium", text: "Vừa" };
      return { class: "good", text: "Thấp" };
  };
  const trafficInfo = getBadgeInfo(risks.traffic_level, "traffic");
  const crowdInfo = getBadgeInfo(risks.crowd_level, "crowd");

  // Minh chứng
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
            <div class="status-item">
                <span class="status-label">🚦 Kẹt xe</span>
                <span class="status-badge ${trafficInfo.class}">${trafficInfo.text}</span>
            </div>
            <div class="status-item">
                <span class="status-label">👥 Đám đông</span>
                <span class="status-badge ${crowdInfo.class}">${crowdInfo.text}</span>
            </div>
        </div>
        
        <div style="margin-top:10px; font-size:11px; color:#888; text-align:center;">
            💡 Mẹo: Bấm vào các đường trên bản đồ để xem thông số chi tiết.
        </div>
    </div>
  `;
}

// Các hàm phụ (Clear, Marker) giữ nguyên như cũ
function clearMapLayers() {
    routeLayers.forEach(layer => map.removeLayer(layer));
    routeLayers = [];
    if (startMarker) map.removeLayer(startMarker);
    if (endMarker) map.removeLayer(endMarker);
}
function drawMarkers(start, end) { /* Giữ nguyên code cũ */ 
    const startIcon = L.divIcon({className: "custom-div-icon", html: `<div class="start-marker">🚀</div>`, iconSize: [36, 36], iconAnchor: [18, 42], popupAnchor: [0, -40]});
    startMarker = L.marker(start, {icon: startIcon}).addTo(map).bindPopup("<b>Điểm đi</b>");
    const endIcon = L.divIcon({className: "custom-div-icon", html: `<div class="end-marker">🏁</div>`, iconSize: [36, 36], iconAnchor: [18, 42], popupAnchor: [0, -40]});
    endMarker = L.marker(end, {icon: endIcon}).addTo(map).bindPopup("<b>Điểm đến</b>");
}