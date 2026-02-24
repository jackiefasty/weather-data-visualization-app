"""
SMHI API Client Module
Handles all communication with the SMHI Open Data API for weather forecasts.
"""

import httpx


# SMHI Forecast API base URL (pmp3g = Meteorological Forecast Product, 3km resolution)
SMHI_FORECAST_BASE = "https://opendata-download-metfcst.smhi.se"
SMHI_FORECAST_VERSION = "2"


def _candidate_points(lon: float, lat: float) -> list[tuple[float, float]]:
    """
    Generate a small set of nearby coordinates to probe SMHI's grid.
    SMHI's pmp3g endpoint sometimes 404s for very precise coordinates
    even inside the coverage area, but works when rounded/snapped.
    """
    points: set[tuple[float, float]] = set()

    def add(l: float, a: float) -> None:
        # Normalize to 6 decimals to keep the set small and stable
        points.add((round(l, 6), round(a, 6)))

    # Original coordinate
    add(lon, lat)

    # Rounded variants
    for prec in (4, 3, 2):
        add(round(lon, prec), round(lat, prec))

    # Small offsets around each base point to step between grid cells
    base_points = list(points)
    offsets = [(0.02, 0.0), (-0.02, 0.0), (0.0, 0.02), (0.0, -0.02)]
    for blon, blat in base_points:
        for dlon, dlat in offsets:
            add(blon + dlon, blat + dlat)

    return list(points)


def call_smhi_forecast_api(lon: float, lat: float) -> dict:
    """
    Fetch meteorological forecast data from SMHI API for a specific location.

    SMHI's pmp3g point endpoint can return 404 for some precise coordinates
    that are still within the Nordic coverage. To make the API more robust,
    this function probes a small set of nearby candidate points (rounded and
    slightly offset) and returns the first successful response.

    Raises:
        httpx.HTTPStatusError: if all candidate points fail with HTTP errors
    """
    last_exc: httpx.HTTPStatusError | None = None

    with httpx.Client(timeout=30.0) as client:
        for clong, clat in _candidate_points(lon, lat):
            url = (
                f"{SMHI_FORECAST_BASE}/api/category/pmp3g/version/{SMHI_FORECAST_VERSION}"
                f"/geotype/point/lon/{clong}/lat/{clat}/data.json"
            )
            try:
                resp = client.get(url)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                # For non-404 errors (e.g. 500, 503) fail fast
                if exc.response.status_code != 404:
                    raise

    if last_exc is not None:
        # Surface the last HTTP error (typically 404) to the caller
        raise last_exc
    raise httpx.HTTPError("SMHI request failed without any HTTP response")


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
