// js/find_route.js

// Biến lưu trữ layer đường đi hiện tại để xóa khi tìm đường mới
let currentRouteLayer = null;
let startMarker = null;
let endMarker = null;

const API_URL = "http://127.0.0.1:5000/api/find-routes"; // Địa chỉ Backend Flask

document.getElementById("searchBtn").addEventListener("click", async () => {
  const startInput = document.getElementById("startPoint");
  const endInput = document.getElementById("endPoint");
  const statusArea = document.getElementById("status-area");

  // 1. LẤY TỌA ĐỘ TỪ DATASET (Được gán bởi search.js)
  const startLat = startInput.dataset.lat;
  const startLon = startInput.dataset.lon;
  const endLat = endInput.dataset.lat;
  const endLon = endInput.dataset.lon;

  // Validate dữ liệu
  if (!startLat || !startLon || !endLat || !endLon) {
    alert("Vui lòng chọn địa điểm từ danh sách gợi ý!");
    return;
  }

  // UI: Hiển thị trạng thái đang tải
  statusArea.innerHTML = `
    <div class="status-box loading">
        ⏳ Đang tính toán lộ trình an toàn...
    </div>`;

  try {
    // 2. GỌI API BACKEND
    const payload = {
      start: [parseFloat(startLat), parseFloat(startLon)],
      end: [parseFloat(endLat), parseFloat(endLon)],
    };

    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (response.status !== 200 || data.status === "error") {
      throw new Error(data.message || "Lỗi không xác định từ Server");
    }

    // 3. VẼ ĐƯỜNG ĐI LÊN BẢN ĐỒ
    drawRouteOnMap(data.geometry, [startLat, startLon], [endLat, endLon]);

    // 4. HIỂN THỊ KẾT QUẢ RA SIDEBAR
    displayRouteInfo(data, statusArea);
  } catch (error) {
    console.error("Lỗi:", error);
    statusArea.innerHTML = `
        <div class="status-box error">
            ❌ <b>Lỗi:</b> ${error.message} <br>
            Hãy chắc chắn Backend Flask đang chạy!
        </div>`;
  }
});

// --- HÀM PHỤ TRỢ: VẼ MAP ---
function drawRouteOnMap(geometry, startCoords, endCoords) {
  // Xóa đường cũ nếu có
  if (currentRouteLayer) map.removeLayer(currentRouteLayer);
  if (startMarker) map.removeLayer(startMarker);
  if (endMarker) map.removeLayer(endMarker);

  // Geometry từ backend là [[lat, lon], [lat, lon]...] -> Leaflet hiểu được ngay
  // Màu đường đi: Xanh (Mặc định) hoặc Cam (Nếu có cảnh báo)
  currentRouteLayer = L.polyline(geometry, {
    color: "#007bff", // Màu xanh dương chủ đạo
    weight: 5,
    opacity: 0.8,
    lineJoin: "round",
  }).addTo(map);

  // 1. Tạo Marker Điểm Bắt Đầu (Start)
  const startIcon = L.divIcon({
    className: "custom-div-icon", // Reset style
    html: `<div class="start-marker">🚀</div>`, // Dùng icon tên lửa hoặc mũi tên
    iconSize: [36, 36], // Kích thước Marker
    iconAnchor: [18, 42], // Canh chỉnh để mũi nhọn trỏ đúng vị trí
    popupAnchor: [0, -40], // Popup hiện phía trên
  });
  startMarker = L.marker(startCoords, { icon: startIcon })
    .addTo(map)
    .bindPopup("<b>Điểm bắt đầu</b>");

  // 2. Tạo Marker Điểm Kết Thúc (End)
  const endIcon = L.divIcon({
    className: "custom-div-icon",
    html: `<div class="end-marker">🏁</div>`, // Dùng icon cờ đích
    iconSize: [36, 36],
    iconAnchor: [18, 42],
    popupAnchor: [0, -40],
  });
  endMarker = L.marker(endCoords, { icon: endIcon })
    .addTo(map)
    .bindPopup("<b>Điểm đến</b>");

  // Zoom bản đồ vừa vặn với đường đi
  map.fitBounds(currentRouteLayer.getBounds(), { padding: [50, 50] });
}

// --- HÀM PHỤ TRỢ: HIỂN THỊ THÔNG TIN ---
function displayRouteInfo(data, container) {
  const risks = data.risk_summary || {};
  const details = data.hit_details || { disasters: [], weathers: [] };

  // 1. Xử lý HTML cho Cảnh báo (Weather + Disaster)
  let warningHtml = "";

  // A. Cảnh báo Thiên tai (Màu Đỏ)
  if (risks.disaster_warning && details.disasters.length > 0) {
    warningHtml += `
      <div class="warning-item disaster">
        <div class="warning-icon">🌋</div>
        <div class="warning-content">
            <strong>Cảnh báo Thiên tai:</strong><br>
            ${details.disasters.join(", ")}
        </div>
      </div>`;
  }

  // B. Cảnh báo Thời tiết (Màu Vàng)
  if (risks.weather_warning && details.weathers.length > 0) {
    warningHtml += `
      <div class="warning-item weather">
        <div class="warning-icon">⛈️</div>
        <div class="warning-content">
            <strong>Cảnh báo Thời tiết:</strong><br>
            ${details.weathers.join(", ")}
        </div>
      </div>`;
  }

  // C. Nếu không có cảnh báo nào -> Hiện badge an toàn
  if (warningHtml === "") {
    warningHtml = `
      <div class="safe-badge">
        ✅ Lộ trình an toàn, không có rủi ro lớn.
      </div>`;
  }

  // 2. Xử lý Badge cho Giao thông & Đám đông
  // Giao thông
  const trafficClass = risks.traffic_level === "High" ? "bad" : "good";
  const trafficText =
    risks.traffic_level === "High" ? "Kẹt xe" : "Thông thoáng";

  // Đám đông
  const crowdClass = risks.crowd_level === "High" ? "bad" : "good";
  const crowdText = risks.crowd_level === "High" ? "Đông đúc" : "Vắng vẻ";

  // 3. Render ra HTML
  container.innerHTML = `
    <div class="result-card">
        <div class="route-stats">
            <div class="stat">
                <span class="value">${data.distance_km}</span>
                <span class="label">KM</span>
            </div>
            <div class="divider-vertical"></div>
            <div class="stat">
                <span class="value">${data.duration_min}</span>
                <span class="label">PHÚT</span>
            </div>
        </div>
        
        <div class="risk-section">
            ${warningHtml}
        </div>
        
        <div class="status-grid">
            <div class="status-item">
                <span class="status-label">🚦 Giao thông</span>
                <span class="status-badge ${trafficClass}">${trafficText}</span>
            </div>
            <div class="status-item">
                <span class="status-label">👥 Điểm nóng</span>
                <span class="status-badge ${crowdClass}">${crowdText}</span>
            </div>
        </div>
    </div>
  `;
}
