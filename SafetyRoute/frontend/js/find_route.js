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

    window.currentRouteData = data;

    // 3. VẼ ĐƯỜNG ĐI LÊN BẢN ĐỒ
    drawRouteOnMap(data.geometry, [startLat, startLon], [endLat, endLon]);

    // 4. VẼ CÁC LỚP BẢN ĐỒ LIÊN QUAN (Đã lọc từ Backend)
    if (data.map_data && typeof drawLayers === "function") {
        console.log("🗺️ Cập nhật bản đồ với dữ liệu vùng quét...");
        drawLayers(data.map_data); // Gọi hàm từ layers.js
    }

    // 5. HIỂN THỊ KẾT QUẢ RA SIDEBAR
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

  // Vẽ đường đi
  currentRouteLayer = L.polyline(geometry, {
    color: "#007bff", // Màu xanh dương chủ đạo
    weight: 5,
    opacity: 0.8,
    lineJoin: "round",
  }).addTo(map);

  // Marker Start
  const startIcon = L.divIcon({
    className: "custom-div-icon",
    html: `<div class="start-marker">🚀</div>`,
    iconSize: [36, 36],
    iconAnchor: [18, 42],
    popupAnchor: [0, -40],
  });
  startMarker = L.marker(startCoords, { icon: startIcon })
    .addTo(map)
    .bindPopup("<b>Điểm bắt đầu</b>");

  // Marker End
  const endIcon = L.divIcon({
    className: "custom-div-icon",
    html: `<div class="end-marker">🏁</div>`,
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
  const summary = data.summary || {};
  const risks = data.risk_summary || {};

  // 1. Xác định màu sắc và icon dựa trên kết quả từ Backend
  // Backend trả về: "green", "yellow", "red"
  let badgeClass = "safe-badge"; // Mặc định xanh
  let icon = "✅";

  if (summary.safety_color === "red") {
    badgeClass = "danger-badge";
    icon = "⛔";
  } else if (summary.safety_color === "yellow") {
    badgeClass = "warning-badge";
    icon = "⚠️";
  }

  // 2. Tạo HTML hiển thị cảnh báo (Lấy trực tiếp text từ Backend)
  const warningHtml = `
      <div class="${badgeClass}">
        <div style="font-size: 16px; margin-bottom: 4px;">
            ${icon} <strong>${summary.safety_label}</strong>
        </div>
        <div style="font-size: 13px; opacity: 0.9;">
            ${summary.description}
        </div>
      </div>`;

  // 3. Xử lý Badge Giao thông & Đám đông (Hỗ trợ 3 cấp độ: High/Medium/Low)
  
  const getBadgeInfo = (level, type) => {
      if (level === "High") return { class: "bad", text: type === "traffic" ? "Kẹt xe" : "Đông đúc" };
      if (level === "Medium") return { class: "medium", text: type === "traffic" ? "Đông nhẹ" : "Vừa phải" };
      // Default Low
      return { class: "good", text: type === "traffic" ? "Thông thoáng" : "Vắng vẻ" };
  };

  const trafficInfo = getBadgeInfo(risks.traffic_level, "traffic");
  const crowdInfo = getBadgeInfo(risks.crowd_level, "crowd");

  // 4. Render ra HTML
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
                <span class="status-badge ${trafficInfo.class}">${trafficInfo.text}</span>
            </div>
            <div class="status-item">
                <span class="status-label">👥 Điểm nóng</span>
                <span class="status-badge ${crowdInfo.class}">${crowdInfo.text}</span>
            </div>
        </div>
    </div>
  `;
}