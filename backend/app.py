"""
Weather Data Visualization Backend
FastAPI application serving weather data from SMHI API with geocoding support.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import httpx

from api_client import get_forecast_for_location, call_smhi_forecast_api
from geocoding import geocode_address
from ml_model import AtmosphericPatternModel


app = FastAPI(
    title="Weather Data Visualization API",
    description="API for cloud cover and lightning probability visualization using SMHI data",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize ML model (lazy load on first use)
_ml_model: Optional[AtmosphericPatternModel] = None


def get_ml_model() -> AtmosphericPatternModel:
    global _ml_model
    if _ml_model is None:
        _ml_model = AtmosphericPatternModel()
    return _ml_model


@app.get("/")
def root():
    return {"message": "Weather Data Visualization API", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/search")
def search_location(q: str = Query(..., min_length=2)):
    """Search for locations by address, city, ZIP, coordinates, etc."""
    try:
        results = geocode_address(q)
        if not results:
            raise HTTPException(status_code=404, detail="No locations found")
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather")
def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """
    Get cloud cover and lightning probability forecast for coordinates.
    SMHI API covers Nordic region - locations far from Sweden may have limited data.
    """
    try:
        data = get_forecast_for_location(lon, lat)
        return data
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="SMHI has no forecast for this location (likely outside Nordic coverage).",
            )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/weather/by-address")
def get_weather_by_address(q: str = Query(..., min_length=2)):
    """Get weather for first matching location from address search."""
    results = geocode_address(q, limit=5)

    # Filter for countries SMHI supports best
    nordic = [r for r in results if r.get("country_code") in {"se", "no", "fi", "dk"}]
    if nordic:
        loc = nordic[0]
    elif results:
        loc = results[0]  # fallback to best global match
    else:
        raise HTTPException(status_code=404, detail="Location not found.")
    try:
        data = get_forecast_for_location(loc["lon"], loc["lat"])
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            # SMHI has no forecast for this lat/lon (outside Nordic region), so we return a 404
            raise HTTPException(status_code=404, detail="SMHI has no forecast for this location (likely outside Nordic coverage).")
        # Other HTTP errors still bubble up as 500, so we also handle that
        raise
    data["location"] = loc.get("display_name", "")
    return data


@app.get("/api/ai-patterns")
def get_ai_patterns(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
):
    """
    Get AI-identified atmospheric patterns for a location.
    Uses a deep learning model trained on SMHI historical data.
    """
    try:
        raw_data = call_smhi_forecast_api(lon, lat)
        model = get_ml_model()
        patterns = model.analyze_forecast(raw_data)
        return patterns
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="SMHI has no forecast for this location (likely outside Nordic coverage).",
            )
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
