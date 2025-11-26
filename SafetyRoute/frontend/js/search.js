// js/search.js

/**
 * HÀM 1: GỌI API TÌM KIẾM (NOMINATIM - OPENSTREETMAP)
 * Trả về danh sách các địa điểm phù hợp
 */
async function searchLocation(query) {
  if (!query || query.length < 3) return [];

  // --- TỐI ƯU HÓA API NOMINATIM ---
  // 1. &accept-language=vi: Bắt buộc trả về tiếng Việt
  // 2. &countrycodes=vn: Chỉ tìm ở VN
  // 3. &viewbox=...: Ưu tiên tìm trong TP.HCM (để kết quả chính xác hơn)
  // 4. &bounded=1: Chỉ tìm trong viewbox (nếu muốn cứng rắn)

  const bboxHCM = "106.33,11.16,107.02,10.37"; // Tọa độ bao quanh TP.HCM

  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
    query
  )}&countrycodes=vn&accept-language=vi&viewbox=${bboxHCM}&bounded=0&limit=5`;

  try {
    const response = await fetch(url);
    const data = await response.json();

    // Map lại dữ liệu cho gọn
    return data.map((item) => ({
      display_name: item.display_name,
      lat: item.lat,
      lon: item.lon,
    }));
  } catch (error) {
    console.error("Lỗi tìm kiếm:", error);
    return [];
  }
}

/**
 * HÀM 2: CẬP NHẬT VỊ TRÍ DROPDOWN
 * Giúp dropdown luôn bám theo input dù scroll hay resize
 */
function updateDropdownPosition(inputElement, listElement) {
  if (!listElement.classList.contains("show")) return;

  const rect = inputElement.getBoundingClientRect();

  // Set vị trí fixed theo viewport
  listElement.style.position = "fixed";
  listElement.style.top = `${rect.bottom + 5}px`; // Cách input 5px
  listElement.style.left = `${rect.left}px`;
  listElement.style.width = `${rect.width}px`;
}

/**
 * HÀM 3: HIỂN THỊ GỢI Ý LÊN GIAO DIỆN
 */
function showSuggestions(inputElement, listElement, results) {
  listElement.innerHTML = ""; // Xóa kết quả cũ

  if (!results || results.length === 0) {
    listElement.classList.remove("show");
    return;
  }

  results.forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item.display_name; // Tên đầy đủ của địa điểm

    // Sự kiện khi click chọn một địa điểm
    li.addEventListener("click", () => {
      inputElement.value = item.display_name; // Điền tên vào ô input
      listElement.classList.remove("show"); // Ẩn danh sách

      // Lưu toạ độ vào dataset của ô input để dùng cho việc vẽ đường sau này
      inputElement.dataset.lat = item.lat;
      inputElement.dataset.lon = item.lon;

      console.log(`Đã chọn: ${item.display_name} [${item.lat}, ${item.lon}]`);
    });

    listElement.appendChild(li);
  });

  listElement.classList.add("show");
  updateDropdownPosition(inputElement, listElement);
}

/**
 * HÀM 4: DEBOUNCE
 * Giúp chờ người dùng gõ xong mới gọi API (tránh spam request)
 * Đã giảm xuống 300ms cho mượt hơn
 */
function debounce(func, timeout = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      func.apply(this, args);
    }, timeout);
  };
}

/**
 * HÀM 5: KHỞI TẠO SỰ KIỆN (MAIN)
 * Chạy khi trang web đã load xong HTML
 */
document.addEventListener("DOMContentLoaded", () => {
  // Helper để gắn logic cho từng cặp input/list
  function setupSearch(inputId, listId) {
    const input = document.getElementById(inputId);
    const list = document.getElementById(listId);

    if (!input || !list) return;

    // Xử lý khi gõ
    input.addEventListener(
      "input",
      debounce(async (e) => {
        const query = e.target.value;
        if (query.length < 3) {
          list.classList.remove("show");
          return;
        }

        // Hiển thị trạng thái đang tìm (Optional UX)
        // list.innerHTML = '<li class="loading">Đang tìm...</li>';
        // list.classList.add("show");
        // updateDropdownPosition(input, list);

        const results = await searchLocation(query);
        showSuggestions(input, list, results);
      }, 300)
    );

    // Cập nhật vị trí khi scroll hoặc resize
    window.addEventListener(
      "scroll",
      () => updateDropdownPosition(input, list),
      true
    );
    window.addEventListener("resize", () =>
      updateDropdownPosition(input, list)
    );

    // Ẩn khi click ra ngoài
    document.addEventListener("click", (e) => {
      if (!input.contains(e.target) && !list.contains(e.target)) {
        list.classList.remove("show");
      }
    });

    // Ẩn khi focus out (nếu cần, nhưng click out đã bao phủ)
    // input.addEventListener("blur", () => setTimeout(() => list.classList.remove("show"), 200));
  }

  setupSearch("startPoint", "start-results");
  setupSearch("endPoint", "end-results");
});
