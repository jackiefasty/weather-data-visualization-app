# Weather Data Visualization App – Technical Description

## Overview

A full-stack application that visualizes **cloud cover** and **lightning probability** for a specific location, using data from the SMHI (Swedish Meteorological and Hydrological Institute) Open Data API. The app includes:

- **Frontend**: React + TypeScript with search bar and interactive charts
- **Backend**: Python (FastAPI) with SMHI API integration
- **Geocoding**: Nominatim (OpenStreetMap) for address → coordinates
- **AI feature**: Deep learning model for atmospheric pattern recognition
- **Deployment**: Terraform (AWS)
- **CI/CD**: GitHub Actions

Limitation: The app is only able to show data from and within the Nordic region. Outisde it it will show "Location not found"

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  React Frontend │────▶│  Python Backend │────▶│   SMHI API      │
│  (Vite/TS)      │     │  (FastAPI)      │     │   (Forecast)    │
└────────┬────────┘     └────────┬────────┘     └─────────────────┘
         │                       │
         │                       ├──────────────▶ Nominatim (Geocoding)
         │                       │
         │                       └──────────────▶ ML Model (PyTorch)
         │
         └──────────────────────▶ /api/* (proxy to backend)
```

## File & Directory Structure

```
weather-data-visualization-app/
├── backend/
│   ├── api_client.py      # SMHI API calling functions
│   ├── geocoding.py       # Nominatim geocoding (address ↔ coordinates)
│   ├── ml_model.py        # Deep learning atmospheric pattern model
│   ├── app.py             # FastAPI application
│   ├── train_model.py     # Script to train ML model on SMHI data
│   ├── requirements.txt   # Python dependencies
│   ├── Dockerfile         # Container image for deployment
│   ├── models/            # Saved ML model weights (gitignored)
│   └── tests/
│       ├── __init__.py
│       └── test_api_client.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.tsx       # Location search input
│   │   │   ├── WeatherCharts.tsx   # Cloud cover & lightning charts
│   │   │   └── AIPatternsPanel.tsx # AI pattern analysis display
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── types.ts
│   │   ├── index.css
│   │   └── App.css
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── terraform/
│   ├── main.tf           # AWS resources (ECR, S3)
│   ├── variables.tf      # Terraform variables
│   └── backend.tf.example
├── .github/
│   └── workflows/
│       └── ci-cd.yml     # GitHub Actions pipeline
├── technical-description.md
└── README.md
```

## API Client (`backend/api_client.py`)

The SMHI API client provides:

- **`call_smhi_forecast_api(lon, lat)`** – Raw HTTP call to SMHI forecast API
- **`extract_cloud_cover_and_lightning(data)`** – Parses response into cloud cover (%) and lightning probability (%)
- **`get_forecast_for_location(lon, lat)`** – Returns processed time series

**SMHI forecast API endpoint:**
```
https://opendata-download-metfcst.smhi.se/api/category/pmp3g/version/2/geotype/point/lon/{lon}/lat/{lat}/data.json
```

**Parameters used:**
- `tcc_mean` – Total cloud cover (octas 0–8) → converted to percentage
- `tstm` – Thunderstorm/lightning probability (%)

## Search Bar

The search bar supports:

- **Coordinates**: `58.0, 16.0` or `58.0 16.0`
- **Address**: street, number, city, region
- **Postal/ZIP code**
- **City name**

Geocoding is done via Nominatim (OpenStreetMap), which returns candidates for selection.

## Charts

- **Cloud Cover (%)** – Area chart over time
- **Lightning Probability (%)** – Area chart over time
- **Aggregation**: Hourly, Daily, Monthly (dd/mm/yyyy or aggregated)

Charts use Recharts with a dark theme.

## AI Feature

The **atmospheric pattern model** is a PyTorch neural network that:

1. Extracts features from SMHI forecast data (temperature, humidity, pressure, cloud cover, lightning probability, wind, precipitation, visibility)
2. Identifies patterns: convective risk, stable atmosphere, frontal passage, moisture buildup, variable conditions
3. Outputs a convective/lightning risk score

**Training**: `python backend/train_model.py` – Fetches SMHI data for Nordic locations and trains the model. The model is saved to `backend/models/`.

## CI/CD (GitHub Actions)

- **Backend**: Lint, test, optional Ruff
- **Frontend**: Install deps, build
- **Terraform**: Validate (on main branch)

## Terraform Deployment

- **ECR**: Repository for backend Docker image
- **S3**: Bucket for frontend static assets

Configure remote backend with `backend.tf` (see `backend.tf.example`).

## Local Development

1. **Backend**  
   ```bash
   cd backend && pip install -r requirements.txt && uvicorn app:app --reload --port 8000
   ```

2. **Frontend**  
   ```bash
   cd frontend && npm install && npm run dev
   ```

3. **Proxy**: Vite proxies `/api` to `http://localhost:8000`.

## SMHI API Coverage

SMHI forecast data covers the **Nordic region** (Sweden, Norway, Finland, Denmark, Baltic). Locations far from this area may return limited or no data.
