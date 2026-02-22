"""
SMHI API Client Module
Handles all communication with the SMHI Open Data API for weather forecasts.
"""

import httpx


# SMHI Forecast API base URL (pmp3g = Meteorological Forecast Product, 3km resolution)
SMHI_FORECAST_BASE = "https://opendata-download-metfcst.smhi.se"
SMHI_FORECAST_VERSION = "2"


def call_smhi_forecast_api(lon: float, lat: float) -> dict:
    """
    Fetch meteorological forecast data from SMHI API for a specific location.
    
    The SMHI forecast API returns hourly forecasts including:
    - tcc_mean: Total cloud cover (octas, 0-8)
    - tstm: Thunderstorm/lightning probability (percent)
    - lcc_mean, mcc_mean, hcc_mean: Low, medium, high cloud cover
    
    Args:
        lon: Longitude (WGS84)
        lat: Latitude (WGS84)
        
    Returns:
        dict: Raw JSON response from SMHI API
        
    Raises:
        httpx.HTTPError: When API request fails
    """
    url = (
        f"{SMHI_FORECAST_BASE}/api/category/pmp3g/version/{SMHI_FORECAST_VERSION}"
        f"/geotype/point/lon/{lon}/lat/{lat}/data.json"
    )
    
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        return response.json()


def extract_cloud_cover_and_lightning(data: dict) -> list[dict]:
    """
    Extract cloud cover and lightning probability from SMHI forecast response.
    
    Args:
        data: Raw response from call_smhi_forecast_api
        
    Returns:
        List of dicts with keys: timestamp, cloud_cover_pct, lightning_prob_pct
    """
    results = []
    
    for time_point in data.get("timeSeries", []):
        valid_time = time_point.get("validTime", "")
        params = {p["name"]: p["values"][0] for p in time_point.get("parameters", [])}
        
        # tcc_mean is in octas (0-8), convert to percentage (0-100)
        cloud_octas = params.get("tcc_mean", 0)
        cloud_cover_pct = min(100, (cloud_octas / 8) * 100)
        
        # tstm = thunderstorm probability in percent (-9 means N/A)
        lightning_prob = params.get("tstm", -9)
        if lightning_prob == -9:
            lightning_prob = 0  # Treat N/A as 0 for visualization
        
        results.append({
            "timestamp": valid_time,
            "cloud_cover_pct": round(cloud_cover_pct, 1),
            "lightning_prob_pct": max(0, lightning_prob),
        })
    
    return results


def get_forecast_for_location(lon: float, lat: float) -> dict:
    """
    Get processed cloud cover and lightning forecast for a location.
    
    Args:
        lon: Longitude
        lat: Latitude
        
    Returns:
        dict with approvedTime, referenceTime, coordinates, and time_series data
    """
    raw_data = call_smhi_forecast_api(lon, lat)
    time_series = extract_cloud_cover_and_lightning(raw_data)
    
    geometry = raw_data.get("geometry", {})
    coords = geometry.get("coordinates", [[0, 0]])[0]
    
    return {
        "approvedTime": raw_data.get("approvedTime"),
        "referenceTime": raw_data.get("referenceTime"),
        "longitude": coords[0] if len(coords) > 0 else lon,
        "latitude": coords[1] if len(coords) > 1 else lat,
        "time_series": time_series,
    }
