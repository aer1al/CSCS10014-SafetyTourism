// js/layers.js

// Chỉ giữ lại 2 layer này
const disasterLayer = L.layerGroup();
const crowdLayer = L.layerGroup();

function drawLayers(data) {
  disasterLayer.clearLayers();
  crowdLayer.clearLayers();

  // 1. VẼ THIÊN TAI (Giữ lại Bão/Lũ nếu có)
  if (data.disasters && data.disasters.length > 0) {
    data.disasters.forEach((zone) => {
      // Vòng tròn đỏ nhạt cảnh báo vùng nguy hiểm
      L.circle([zone.lat, zone.lng], {
        color: "#e74c3c", weight: 0, 
        fillColor: "#e74c3c", fillOpacity: 0.2,
        radius: (zone.radius || 5) * 1000,
      }).addTo(disasterLayer);

      // Icon Tâm bão (Pulse)
      const pulseIcon = L.divIcon({
        className: "custom-div-icon",
        html: `<div class="pulse-icon-wrapper"><div class="pulse-core"></div><div class="pulse-ring"></div></div>`,
        iconSize: [20, 20], iconAnchor: [10, 10],
      });
      L.marker([zone.lat, zone.lng], { icon: pulseIcon })
        .bindPopup(`<b style="color:#c0392b">🌋 ${zone.name}</b>`).addTo(disasterLayer);
    });
  }

  // 2. VẼ ĐÁM ĐÔNG
  if (data.crowd && data.crowd.length > 0) {
    data.crowd.forEach((zone) => {
        const cleanIcon = L.divIcon({
          className: "custom-div-icon",
          html: `<div class="crowd-marker"></div>`,
          iconSize: [12, 12], iconAnchor: [6, 6],
        });
        L.marker([zone.lat, zone.lng], { icon: cleanIcon })
          .bindPopup(`<b>👥 ${zone.name}</b>`).addTo(crowdLayer);
    });
  }

  // Mặc định bật layer Thiên tai và Đám đông
  if (window.map) {
      window.map.addLayer(disasterLayer);
      window.map.addLayer(crowdLayer);
  }
}

// Xử lý sự kiện Toggle (Nút bật tắt góc trên)
document.addEventListener("DOMContentLoaded", () => {
    // Gọi API lấy dữ liệu map lần đầu
    fetch("http://127.0.0.1:5000/api/map-data")
        .then(res => res.json())
        .then(json => {
            if(json.status === "success") drawLayers(json.data);
        })
        .catch(e => console.error(e));

    const chkDisaster = document.getElementById("chk-disaster");
    const chkCrowd = document.getElementById("chk-crowd");

    // Toggle Thiên tai
    if(chkDisaster) {
        chkDisaster.addEventListener("change", (e) => {
            if (e.target.checked) window.map.addLayer(disasterLayer);
            else window.map.removeLayer(disasterLayer);
        });
    }

    // Toggle Đám đông
    if(chkCrowd) {
        chkCrowd.addEventListener("change", (e) => {
            if (e.target.checked) window.map.addLayer(crowdLayer);
            else window.map.removeLayer(crowdLayer);
        });
    }
    
    // Nút "Thời tiết" giờ vô dụng vì ta đã xóa radar, nhưng cứ để đó cho đẹp giao diện hoặc ẩn đi bằng CSS nếu muốn.
});