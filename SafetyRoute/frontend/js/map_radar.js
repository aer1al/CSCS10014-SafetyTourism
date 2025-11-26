// js/map_radar.js

const map = L.map("map").setView([10.7769, 106.7009], 10);
window.map = map;

// --- DÙNG CARTO POSITRON (Giao diện sáng, tối giản) ---
L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: "abcd",
    maxZoom: 20,
  }
).addTo(map);

// Khởi tạo biến toàn cục để file khác gọi được
window.radarLayer = null;

// --- XỬ LÝ SIDEBAR ---
const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggleBtn");

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");
  toggleBtn.innerHTML = sidebar.classList.contains("collapsed") ? "▶" : "◀";
  setTimeout(() => map.invalidateSize(), 300);
}

if (toggleBtn) toggleBtn.addEventListener("click", toggleSidebar);

// --- TÍCH HỢP RADAR ---
function addRadarLayer(ts) {
  const radarUrl = `https://tilecache.rainviewer.com/v2/radar/${ts}/256/{z}/{x}/{y}/2/1_1.png`;

  // 1. GÁN VÀO BIẾN (Chưa thêm vào map vội)
  window.radarLayer = L.tileLayer(radarUrl, {
    tileSize: 256,
    opacity: 0.7,
    zIndex: 100,
    maxNativeZoom: 10,
    maxZoom: 18,
  });

  // 2. KIỂM TRA CHECKBOX RỒI MỚI VẼ
  const weatherChk = document.getElementById("chk-weather");
  if (weatherChk && weatherChk.checked) {
    window.radarLayer.addTo(map);
    console.log("✅ Checkbox đang bật -> Đã vẽ Radar.");
  } else {
    console.log("⏸️ Checkbox đang tắt -> Radar đã tải nhưng chưa vẽ.");
  }
}

// Gọi API RainViewer
fetch("https://api.rainviewer.com/public/weather-maps.json")
  .then((response) => response.json())
  .then((data) => {
    if (data.radar && data.radar.past && data.radar.past.length > 0) {
      const lastPastFrame = data.radar.past[data.radar.past.length - 1];
      addRadarLayer(lastPastFrame.time);
    }
  })
  .catch((error) => console.error("Lỗi RainViewer:", error));
