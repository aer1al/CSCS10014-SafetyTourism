import requests

def get_center_coordinates(address: str):
    """
    Trả về tọa độ trung tâm (lat, lon) của một địa điểm.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1
    }
    headers = {"User-Agent": "SmartTourismSystem/1.0 (contact: duykha.vu09@gmail.com)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        time.sleep(1.1)
        response.raise_for_status()
        data = response.json()

        if not data:
            print("❌ Không tìm thấy địa điểm:", address)
            return None

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)

    except requests.RequestException as e:
        print("⚠️ Lỗi khi gọi Nominatim API:", e)
        return None
