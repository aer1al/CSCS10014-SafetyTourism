// js/layers.js

// Khởi tạo các lớp layer (Layer Group)
const disasterLayer = L.layerGroup();
const weatherLayer = L.layerGroup(); // <-- MỚI: Layer cho thời tiết giả lập
const crowdLayer = L.layerGroup();

function drawLayers(data) {
  console.log("🎨 Đang vẽ lại bản đồ...", data);

  // Xóa layer cũ trước khi vẽ mới
  disasterLayer.clearLayers();
  weatherLayer.clearLayers();
  crowdLayer.clearLayers();

  // --- 1. VẼ THIÊN TAI (MÀU ĐỎ - PULSE) ---
  if (data.disasters && data.disasters.length > 0) {
    data.disasters.forEach((zone) => {
      // Vòng tròn cảnh báo
      L.circle([zone.lat, zone.lng], {
        color: "#e74c3c",
        weight: 1,
        fillColor: "#e74c3c",
        fillOpacity: 0.2,
        radius: (zone.radius || 5) * 1000,
      }).addTo(disasterLayer);

      // Icon tâm bão
      const pulseIcon = L.divIcon({
        className: "custom-div-icon",
        html: `
            <div class="pulse-icon-wrapper">
                <div class="pulse-core"></div>
                <div class="pulse-ring"></div>
                <div class="pulse-ring"></div>
            </div>`,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });

      L.marker([zone.lat, zone.lng], { icon: pulseIcon })
        .bindPopup(`<b style="color:#c0392b">🌋 ${zone.name || zone.title}</b>`)
        .addTo(disasterLayer);
    });
  }

  // --- 2. VẼ THỜI TIẾT (MÀU VÀNG - MỚI) ---
  if (data.weather && data.weather.length > 0) {
    data.weather.forEach((zone) => {
      // Vòng tròn vùng mưa
      L.circle([zone.lat, zone.lng], {
        color: "#f1c40f", // Vàng
        weight: 1,
        fillColor: "#f39c12",
        fillOpacity: 0.2,
        radius: (zone.radius || 3) * 1000,
      }).addTo(weatherLayer);

      // Icon đám mây/mưa (Dùng Emoji cho nhanh)
      const weatherIcon = L.divIcon({
        className: "custom-div-icon",
        html: `<div style="font-size: 24px;">⛈️</div>`,
        iconSize: [30, 30],
        iconAnchor: [15, 15],
      });

      L.marker([zone.lat, zone.lng], { icon: weatherIcon })
        .bindPopup(
          `<b style="color:#d35400">⚠️ ${zone.condition}</b><br>${zone.description}`
        )
        .addTo(weatherLayer);
    });
  }

  // --- 3. VẼ ĐÁM ĐÔNG (MÀU CAM) ---
if (data.crowd && data.crowd.length > 0) {
    data.crowd.forEach((zone) => {
      if (zone.lat && zone.lng) {
        
        // A. Vẽ vùng ảnh hưởng (Radius)
        L.circle([zone.lat, zone.lng], {
            color: "#e67e22",      // Viền cam đậm
            weight: 1,
            fillColor: "#d35400",  // Nền cam cháy
            fillOpacity: 0.15,     // Trong suốt
            radius: (zone.radius || 0.3) * 1000 // Mặc định 300m nếu thiếu
        }).addTo(crowdLayer);

        // B. Vẽ tâm điểm (Icon nhỏ)
        const cleanIcon = L.divIcon({
          className: "custom-div-icon",
          html: `<div class="crowd-marker"></div>`,
          iconSize: [10, 10], // Nhỏ lại xíu cho đỡ rối
          iconAnchor: [5, 5],
        });

        L.marker([zone.lat, zone.lng], { icon: cleanIcon })
          .bindPopup(
            `<div style="text-align:center">
                <b style="color:#d35400">👥 ${zone.name}</b><br>
                <span style="font-size:11px">Bán kính: ${zone.radius || 0.3}km</span>
            </div>`
          )
          .addTo(crowdLayer);
      }
    });
  }

  // --- HIỂN THỊ MẶC ĐỊNH LÊN BẢN ĐỒ ---
  // Sử dụng window.map để đảm bảo biến map tồn tại
  if (window.map) {
    const chkDisaster = document.getElementById("chk-disaster");
    const chkWeather = document.getElementById("chk-weather");
    const chkCrowd = document.getElementById("chk-crowd");

    if (chkDisaster && chkDisaster.checked) window.map.addLayer(disasterLayer);
    // Logic mới: Nút "Thời tiết" sẽ bật cả Radar thật (RainViewer) lẫn Vùng mưa giả lập (Mock)
    if (chkWeather && chkWeather.checked) window.map.addLayer(weatherLayer);
    if (chkCrowd && chkCrowd.checked) window.map.addLayer(crowdLayer);
  }
}

async function fetchMapData() {
  try {
    console.log("📡 Đang tải dữ liệu bản đồ từ Backend...");
    const res = await fetch("http://127.0.0.1:5000/api/map-data");
    const json = await res.json();

    if (json.status === "success") {
      console.log(
        `✅ Đã tải: ${json.data.disasters.length} thiên tai, ${json.data.weather.length} vùng thời tiết.`
      );
      drawLayers(json.data);
    }
  } catch (e) {
    console.error("❌ Lỗi API map-data (Kiểm tra xem Server chạy chưa):", e);
  }
}

// --- LẮNG NGHE SỰ KIỆN TOGGLE ---
document.addEventListener("DOMContentLoaded", () => {
  fetchMapData(); // Gọi ngay khi web load

  const chkWeather = document.getElementById("chk-weather");
  const chkDisaster = document.getElementById("chk-disaster");
  const chkCrowd = document.getElementById("chk-crowd");

  // 1. Toggle Thời tiết (Radar + Mock Weather)
  chkWeather.addEventListener("change", (e) => {
    if (!window.map) return;
    if (e.target.checked) {
      if (window.radarLayer) window.radarLayer.addTo(window.map); // Radar thật
      window.map.addLayer(weatherLayer); // Mock weather
    } else {
      if (window.radarLayer) window.radarLayer.remove();
      window.map.removeLayer(weatherLayer);
    }
  });

  // 2. Toggle Thiên tai
  chkDisaster.addEventListener("change", (e) => {
    if (!window.map) return;
    if (e.target.checked) window.map.addLayer(disasterLayer);
    else window.map.removeLayer(disasterLayer);
  });

  // 3. Toggle Đám đông
  chkCrowd.addEventListener("change", (e) => {
    if (!window.map) return;
    if (e.target.checked) window.map.addLayer(crowdLayer);
    else window.map.removeLayer(crowdLayer);
  });
  // 1. Đọc tham số từ URL (ví dụ: ?type=crowd)
  const params = new URLSearchParams(window.location.search);
  const type = params.get('type'); // Lấy chữ 'crowd', 'weather', hoặc 'flood'

  // 2. Kiểm tra và kích hoạt checkbox tương ứng
  if (type) {
      console.log("📢 Phát hiện yêu cầu bật filter:", type);
      
      let checkboxToClick = null;

      if (type === 'crowd') {
          checkboxToClick = document.getElementById('chk-crowd');
      } 
      else if (type === 'weather') {
          checkboxToClick = document.getElementById('chk-weather');
      } 
      else if (type === 'flood') { 
          // Lưu ý: Bên HTML bạn gọi là 'flood', nhưng ID checkbox là 'chk-disaster'
          checkboxToClick = document.getElementById('chk-disaster');
      }

      // 3. Giả lập cú click chuột để bật layer lên
      if (checkboxToClick) {
          // Phải dùng .click() thay vì .checked = true 
          // để nó kích hoạt luôn sự kiện vẽ bản đồ (change event)
          checkboxToClick.click(); 
      }
  }
});
