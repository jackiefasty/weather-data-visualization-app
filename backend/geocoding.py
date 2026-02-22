"""
Geocoding Module
Converts addresses, coordinates, and location strings to coordinates using Nominatim (OpenStreetMap).
"""

import re
import httpx
from typing import Optional


NOMINATIM_BASE = "https://nominatim.openstreetmap.org"


def geocode_address(query: str, limit: int = 5) -> list[dict]:
    """
    Convert address/location string to coordinates using Nominatim.
    
    Supports:
    - Full addresses (street, number, city, region)
    - ZIP/postal codes
    - City names
    - Region/country names
    - Coordinates in format "lat,lon" or "lat lon"
    
    Args:
        query: Address, city, coordinates, or location string
        limit: Max number of results to return
        
    Returns:
        List of dicts with lat, lon, display_name
    """
    query = query.strip()
    
    # Check if query is already coordinates
    coord_result = _parse_coordinates(query)
    if coord_result:
        return [coord_result]
    
    url = f"{NOMINATIM_BASE}/search"
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
    }
    headers = {"User-Agent": "WeatherDataVisualizationApp/1.0"}
    
    with httpx.Client(timeout=15.0) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        results = response.json()
    
    return [
        {
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
            "display_name": r.get("display_name", ""),
            "type": r.get("type", ""),
            "importance": r.get("importance", 0),
        }
        for r in results
    ]


def reverse_geocode(lat: float, lon: float) -> Optional[dict]:
    """
    Convert coordinates to address using Nominatim reverse geocoding.
    
    Args:
        lat: Latitude
        lon: Longitude
        
    Returns:
        dict with display_name and address components, or None
    """
    url = f"{NOMINATIM_BASE}/reverse"
    params = {"lat": lat, "lon": lon, "format": "json"}
    headers = {"User-Agent": "WeatherDataVisualizationApp/1.0"}
    
    with httpx.Client(timeout=15.0) as client:
        response = client.get(url, params=params, headers=headers)
        response.raise_for_status()
        result = response.json()
    
    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result.get("display_name", ""),
    }


def _parse_coordinates(query: str) -> Optional[dict]:
    """Parse coordinate string like '58.5, 16.0' or '58.5 16.0'."""
    # Match lat,lon or lat lon (with optional spaces)
    patterns = [
        r"^(-?\d+\.?\d*)\s*[,;]\s*(-?\d+\.?\d*)$",
        r"^(-?\d+\.?\d*)\s+(-?\d+\.?\d*)$",
    ]
    for pat in patterns:
        m = re.match(pat, query.strip())
        if m:
            lat, lon = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {
                    "lat": lat,
                    "lon": lon,
                    "display_name": f"Coordinates: {lat}, {lon}",
                }
    return None
