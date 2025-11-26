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

  // Thêm Marker điểm đầu/cuối
  startMarker = L.marker(startCoords).addTo(map).bindPopup("<b>Điểm đi</b>");
  endMarker = L.marker(endCoords).addTo(map).bindPopup("<b>Điểm đến</b>");

  // Zoom bản đồ vừa vặn với đường đi
  map.fitBounds(currentRouteLayer.getBounds(), { padding: [50, 50] });
}

// --- HÀM PHỤ TRỢ: HIỂN THỊ THÔNG TIN ---
function displayRouteInfo(data, container) {
  const risks = data.risk_summary;
  const details = data.hit_details || { disasters: [], weathers: [] };

  let riskHtml = "";
  let isSafe = true;

  // Logic hiển thị cảnh báo
  if (risks.disaster_warning) {
    isSafe = false;
    riskHtml += `<div class="warning-item">🌋 Cảnh báo thiên tai: ${details.disasters.join(
      ", "
    )}</div>`;
  }

  if (risks.weather_warning) {
    isSafe = false;
    riskHtml += `<div class="warning-item">🌧️ Cảnh báo thời tiết: ${details.weathers.join(
      ", "
    )}</div>`;
  }

  if (isSafe) {
    riskHtml = `<div class="safe-badge">✅ Lộ trình an toàn</div>`;
  }

  container.innerHTML = `
    <div class="result-card">
        <div class="route-stats">
            <div class="stat">
                <span class="value">${data.distance_km}</span>
                <span class="label">km</span>
            </div>
            <div class="stat">
                <span class="value">${data.duration_min}</span>
                <span class="label">phút</span>
            </div>
        </div>
        
        <div class="risk-section">
            ${riskHtml}
        </div>
        
        <div class="traffic-info">
            🚦 Mật độ giao thông: <b>${risks.traffic_level || "Bình thường"}</b>
        </div>
    </div>
  `;
}
