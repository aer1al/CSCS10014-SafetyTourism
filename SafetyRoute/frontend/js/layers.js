// js/layers.js

const disasterLayer = L.layerGroup();
const crowdLayer = L.layerGroup();

function drawLayers(data) {
  console.log("🎨 Đang vẽ lại giao diện Cyberpunk...");

  // Xóa layer cũ trước khi vẽ mới (tránh bị chồng lấn nếu gọi nhiều lần)
  disasterLayer.clearLayers();
  crowdLayer.clearLayers();

  // --- 1. VẼ THIÊN TAI (PULSE RADAR STYLE) ---
  if (data.disasters && data.disasters.length > 0) {
    data.disasters.forEach((zone) => {
      // A. Vẽ vòng tròn biên giới (Ranh giới nguy hiểm)
      L.circle([zone.lat, zone.lng], {
        color: "#e74c3c", // Viền đỏ
        weight: 1, // Viền mảnh
        fillColor: "#e74c3c", // Nền đỏ
        fillOpacity: 0.1, // Rất mờ (để không che bản đồ)
        radius: (zone.radius || 5) * 1000,
      }).addTo(disasterLayer);

      // B. Vẽ tâm bão với hiệu ứng Pulse (Nhịp đập)
      const pulseIcon = L.divIcon({
        className: "custom-div-icon", // Class rỗng để reset style mặc định
        html: `
                    <div class="pulse-icon-wrapper">
                        <div class="pulse-core"></div>
                        <div class="pulse-ring"></div>
                        <div class="pulse-ring"></div>
                    </div>
                `,
        iconSize: [20, 20], // Kích thước của tâm
        iconAnchor: [10, 10], // Canh giữa (một nửa của size)
      });

      L.marker([zone.lat, zone.lng], { icon: pulseIcon })
        .bindPopup(
          `
                    <div style="text-align:center">
                        <b style="color:#c0392b; font-size:16px">🌋 ${zone.name}</b><br>
                        <span>Bán kính: ${zone.radius}km</span>
                    </div>
                `
        )
        .addTo(disasterLayer);
    });
  }

  // --- 2. VẼ ĐÁM ĐÔNG (CLEAN STYLE) ---
  if (data.crowd && data.crowd.length > 0) {
    data.crowd.forEach((zone) => {
      if (zone.lat && zone.lng) {
        const cleanIcon = L.divIcon({
          className: "custom-div-icon",
          html: `<div class="crowd-marker"></div>`,

          // 👇 THAY ĐỔI Ở ĐÂY:
          iconSize: [14, 14], // Nhỏ gọn (Cũ là 16x16)
          iconAnchor: [7, 7], // Canh giữa (1/2 kích thước)
        });

        L.marker([zone.lat, zone.lng], { icon: cleanIcon })
          .bindPopup(
            `
                        <div style="text-align:center">
                            <b style="color:#d35400; font-size:14px">👥 ${zone.name}</b><br>
                            <span style="font-size:12px; color:#555">Độ tập trung cao</span>
                        </div>
                    `
          )
          .addTo(crowdLayer);
      }
    });
  }

  // Hiển thị mặc định
  const chkDisaster = document.getElementById("chk-disaster");
  const chkCrowd = document.getElementById("chk-crowd");

  if (chkDisaster && chkDisaster.checked) disasterLayer.addTo(map);
  if (chkCrowd && chkCrowd.checked) crowdLayer.addTo(map);
}

async function fetchMapData() {
  try {
    const res = await fetch("http://127.0.0.1:5000/api/map-data");
    const json = await res.json();
    if (json.status === "success") {
      drawLayers(json.data);
    }
  } catch (e) {
    console.error("❌ Lỗi API map-data:", e);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  fetchMapData();

  const chkWeather = document.getElementById("chk-weather");
  const chkDisaster = document.getElementById("chk-disaster");
  const chkCrowd = document.getElementById("chk-crowd");

  // Sự kiện Weather
  chkWeather.addEventListener("change", (e) => {
    if (!window.radarLayer) return;
    if (e.target.checked) window.radarLayer.addTo(map);
    else window.radarLayer.remove();
  });

  // Sự kiện Disaster
  chkDisaster.addEventListener("change", (e) => {
    if (e.target.checked) map.addLayer(disasterLayer);
    else map.removeLayer(disasterLayer);
  });

  // Sự kiện Crowd
  chkCrowd.addEventListener("change", (e) => {
    if (e.target.checked) map.addLayer(crowdLayer);
    else map.removeLayer(crowdLayer);
  });
});
