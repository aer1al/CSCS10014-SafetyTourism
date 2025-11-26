// --- 1. KHỞI TẠO BẢN ĐỒ ---
// Zoom 10 để thấy toàn bộ TP.HCM
// --- 1. KHỞI TẠO BẢN ĐỒ ---
// Zoom 10 để thấy toàn bộ TP.HCM
const map = L.map("map").setView([10.7769, 106.7009], 10);
window.map = map; // Expose cho các file JS khác dùng chung

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// --- 2. XỬ LÝ SIDEBAR TOGGLE ---
const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggleBtn");

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");

  // Đổi icon mũi tên
  if (sidebar.classList.contains("collapsed")) {
    toggleBtn.innerHTML = "▶";
  } else {
    toggleBtn.innerHTML = "◀";
  }

  // QUAN TRỌNG: Cập nhật lại kích thước bản đồ sau khi Sidebar thay đổi
  // Nếu không có dòng này, bản đồ sẽ không biết nó vừa được mở rộng ra
  setTimeout(() => {
    map.invalidateSize();
  }, 300); // 300ms khớp với thời gian transition trong CSS
}

// Gắn sự kiện click cho nút toggle (vì trong file JS rời không dùng onclick="" trong HTML được)
if (toggleBtn) {
  toggleBtn.addEventListener("click", toggleSidebar);
}

// --- 3. TÍCH HỢP RAIN RADAR ---
function addRadarLayer(ts) {
  const radarUrl = `https://tilecache.rainviewer.com/v2/radar/${ts}/256/{z}/{x}/{y}/2/1_1.png`;
  L.tileLayer(radarUrl, {
    tileSize: 256,
    opacity: 0.7,
    zIndex: 100,
    maxNativeZoom: 10,
    maxZoom: 18,
  }).addTo(map);
  console.log(
    "Đã thêm lớp Radar lúc:",
    new Date(ts * 1000).toLocaleTimeString()
  );
}

// Gọi API RainViewer
fetch("https://api.rainviewer.com/public/weather-maps.json")
  .then((response) => response.json())
  .then((data) => {
    if (data.radar && data.radar.past && data.radar.past.length > 0) {
      // Lấy khung hình quá khứ gần nhất (mới nhất)
      const lastPastFrame = data.radar.past[data.radar.past.length - 1];
      addRadarLayer(lastPastFrame.time);
    }
  })
  .catch((error) => console.error("Lỗi RainViewer:", error));
