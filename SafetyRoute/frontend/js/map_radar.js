// js/map_radar.js

// 1. Khởi tạo Map
// Tắt zoomControl mặc định để chúng ta tự đặt vị trí mới cho đẹp
const map = L.map("map", {
    zoomControl: false 
}).setView([10.7769, 106.7009], 13);

window.map = map;

// 2. Thêm nút Zoom ở GÓC PHẢI DƯỚI (Bottom Right)
// Để nó nằm trên nút Chat một chút, không bị header che
L.control.zoom({
    position: 'topright'
}).addTo(map);

// 3. Bản đồ nền (Carto Positron) - Sáng, đẹp, tối giản
L.tileLayer(
  "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
  {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    subdomains: "abcd",
    maxZoom: 20,
  }
).addTo(map);

// --- XỬ LÝ SIDEBAR (Giữ nguyên) ---
const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggleBtn");

function toggleSidebar() {
  sidebar.classList.toggle("collapsed");
  toggleBtn.innerHTML = sidebar.classList.contains("collapsed") ? "▶" : "◀";
  setTimeout(() => map.invalidateSize(), 300);
}

if (toggleBtn) toggleBtn.addEventListener("click", toggleSidebar);

// --- ĐÃ XÓA PHẦN RAINVIEWER (RADAR) TẠI ĐÂY ---
// Giờ bản đồ sẽ sạch trơn, không còn mây xanh đỏ nữa.
window.radarLayer = null;