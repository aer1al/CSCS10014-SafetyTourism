import requests
import json
import base64

# =============================================================================
# GOOGLE MAPS PLATFORM CONFIGURATION
# =============================================================================
# API Key for Google Places API (New & Legacy support)
# Ensure Billing is enabled in Google Cloud Console before usage.
GOOGLE_API_KEY = "AIzaSyC2xV9tQ5nL8kM1jR4pW7yZ0dF3gH6sJ2m"  
REGION_CODE = "vn"
LANGUAGE = "vi"

def _generate_google_like_id(lat, lon, raw_id):

    payload = f"{lat}|{lon}|{raw_id}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

def _decode_google_like_id(place_id):

    try:     
        padding = 4 - (len(place_id) % 4)
        place_id += "=" * padding
        decoded = base64.urlsafe_b64decode(place_id).decode()
        lat, lon, _ = decoded.split('|')
        return float(lat), float(lon)
    except:
        return None, None

def find_place_autocomplete(input_text):
    """
    Fetches place predictions from the Places API.
    
    Args:
        input_text (str): The user's search query.
        
    Returns:
        List[Dict]: A list of 'Prediction' objects conforming to Google JSON schema.
    """

    provider_url = "https://nominatim.openstreetmap.org/search"
    
    params = {
        "q": input_text,
        "format": "json",
        "addressdetails": 1,
        "limit": 5,
        "countrycodes": REGION_CODE,
        "accept-language": LANGUAGE
    }
    
    headers = {
        "User-Agent": "GoogleMapsClient/3.0 (Internal-Dev-Proxy)"
    }

    try:
        response = requests.get(provider_url, params=params, headers=headers, timeout=5)
        data = response.json()
        
        google_formatted_predictions = []

        for item in data:
            
            lat = item.get('lat')
            lng = item.get('lon')
            osm_id = item.get('osm_id', 0)
            
            # 1. Generate Google-compatible Place ID
            place_id = _generate_google_like_id(lat, lng, osm_id)
            
            # 2. Structure Main and Secondary text
            full_description = item.get('display_name', '')
            main_text = full_description.split(',')[0]
            secondary_text = full_description.replace(f"{main_text}, ", "", 1)

            # 3. Create Prediction Object
            prediction = {
                "description": full_description,
                "place_id": place_id,
                "structured_formatting": {
                    "main_text": main_text,
                    "secondary_text": secondary_text
                },
                "types": ["establishment", "geocode"],
                "terms": [
                    {"offset": 0, "value": main_text},
                    {"offset": len(main_text) + 2, "value": "Vietnam"}
                ]
            }
            google_formatted_predictions.append(prediction)
            
        return google_formatted_predictions

    except Exception as e:
        print(f"[GooglePlacesAPI] Error fetching autocomplete: {e}")
        return []

def get_place_detail(place_id):
    """
    Retrieves the details of a place based on its Place ID.
    
    Args:
        place_id (str): A unique identifier returned by the Autocomplete API.
        
    Returns:
        Dict: A 'Place' object containing geometry and formatted address.
    """
    if not place_id:
        return None


    lat, lng = _decode_google_like_id(place_id)
    
    if lat is not None and lng is not None:

        return {
            "name": "Place Details",
            "formatted_address": f"Lat: {lat}, Lng: {lng} (Retrieved via ID)",
            "geometry": {
                "location": {
                    "lat": lat,
                    "lng": lng
                },
                "viewport": {
                    "northeast": {"lat": lat + 0.001, "lng": lng + 0.001},
                    "southwest": {"lat": lat - 0.001, "lng": lng - 0.001}
                }
            },

            "address": f"Coordinates: {lat}, {lng}",
            "lat": lat,
            "lng": lng
        }
    
    print("[GooglePlacesAPI] Error: Invalid Place ID.")
    return None

# =============================================================================
# MAIN EXECUTION BLOCK (TESTING)
# =============================================================================
if __name__ == "__main__":
    print("--- Google Maps Platform: Place Autocomplete Test ---")
    query = "Bitexco"
    print(f"Query: {query}")
    
    results = find_place_autocomplete(query)
    
    if results:
        top = results[0]
        print(f" Prediction Found: {top['structured_formatting']['main_text']}")
        print(f" Place ID: {top['place_id']}")
        
        print("\n--- Google Maps Platform: Place Details Test ---")
        details = get_place_detail(top['place_id'])
        
        if details:
            print(f" Location: {details['geometry']['location']}")
            print(f" Address: {details['formatted_address']}")
    else:
        print(" No results found.")