import requests
import json

# THAY KEY CỦA BẠN VÀO ĐÂY
ORS_API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6IjlhM2M0MjY3ZmU1MzRkYjlhZDIyZjBiMzBkOTYzYzMxIiwiaCI6Im11cm11cjY0In0=" 

def get_routes_from_mapbox(start_lat, start_lng, end_lat, end_lng):
    """
    Gọi OpenRouteService lấy 3 tuyến đường phân biệt.
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
    
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json; charset=utf-8'
    }
    
    body = {
        "coordinates": [
            [start_lng, start_lat],
            [end_lng, end_lat]
        ],
        "alternative_routes": {
            "target_count": 3,      # Xin 3 đường
            "weight_factor": 2.0,   # Chấp nhận đường chậm gấp 2 lần (để tìm QL cũ)
            "share_factor": 0.6     # Ép các đường phải khác nhau ít nhất 40%
        },
        "preference": "recommended"
    }
    
    try:
        response = requests.post(url, json=body, headers=headers, timeout=15)
        data = response.json()
        features = data.get("features", [])
        
        cleaned_routes = []
        for i, feature in enumerate(features):
            props = feature["properties"]
            summary = props.get("summary", {}).get("value", f"Tuyến đường #{i+1}")

            cleaned_routes.append({
                "id": i,
                "duration": props["summary"]["duration"],
                "distance": props["summary"]["distance"],
                "geometry": feature["geometry"]["coordinates"],
                "summary": summary
            })
            
        return cleaned_routes

    except Exception as e:
        print(f"Lỗi API ORS: {e}")
        return []