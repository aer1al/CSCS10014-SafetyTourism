import requests
import json

def get_crowd_density(lat: float, lon: float, radius_meters: int = 500) -> int:
    """
    Fetches the number of 'high-traffic' POIs around a coordinate using Overpass API.
    Used to estimate crowd density based on venue concentration.

    Target Amenities:
    - Food & Drink: restaurant, cafe, pub, bar, fast_food, marketplace
    - Tourism: attraction, museum, view_point, theme_park, zoo
    - Transport: bus_station, train_station

    Args:
        lat (float): Latitude
        lon (float): Longitude
        radius (int): Search radius in meters (default 500m)
        
    Returns:
        int: Total count of relevant POIs (restaurants, attractions, markets, etc.)
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # regex query for multiple values to keep the query compact
    amenity_regex = "restaurant|cafe|pub|bar|fast_food|marketplace|bus_station"
    tourism_regex = "attraction|museum|viewpoint|theme_park|zoo"
    
    overpass_query = f"""
    [out:json][timeout:5];
    (
      node["amenity"~"{amenity_regex}"](around:{radius_meters},{lat},{lon});
      way["amenity"~"{amenity_regex}"](around:{radius_meters},{lat},{lon});
      node["tourism"~"{tourism_regex}"](around:{radius_meters},{lat},{lon});
      way["tourism"~"{tourism_regex}"](around:{radius_meters},{lat},{lon});
    );
    out count;
    """
    
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=8)
        response.raise_for_status()
        data = response.json()
        
        # Overpass 'out count' returns a slightly different structure
        # We look for the 'elements' array where tags contain the count info
        # usually in the format: {"type": "count", "id": 0, "tags": {"nodes": "X", ...}}
        
        total_poi = 0
        if 'elements' in data:
            for el in data['elements']:
                if 'tags' in el:
                    # Sum up nodes, ways, and relations found
                    total_poi += int(el['tags'].get('nodes', 0))
                    total_poi += int(el['tags'].get('ways', 0))
                    total_poi += int(el['tags'].get('relations', 0))
                    
        return total_poi

    except requests.exceptions.RequestException as e:
        print(f"Error fetching crowd data from Overpass: {e}")
        return 0
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing crowd data: {e}")
        return 0

# Test
if __name__ == "__main__":
    # Test with a busy location (e.g., Ben Thanh Market area)
    count = get_crowd_density(10.7725, 106.6980)
    print(f"POIs found near Ben Thanh: {count}")