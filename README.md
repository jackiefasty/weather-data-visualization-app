# Weather Data Visualization App

A full-stack application for visualizing **cloud cover** and **lightning probability** for any location, powered by the [SMHI Open Data API](https://opendata.smhi.se/apidocs/).

## Features

- **Search bar** – Address, city, postal code, or coordinates (e.g. `Stockholm`, `59.3, 18.0`)
- **Charts** – Cloud cover (%) and lightning probability (%) with hourly/daily/monthly aggregation
- **Geocoding** – Nominatim (OpenStreetMap) for address → coordinates
- **AI patterns** – Deep learning model trained on SMHI data to detect atmospheric patterns
- **CI/CD** – GitHub Actions pipeline
- **Deployment** – Terraform (AWS)

## Tech Stack

| Layer      | Technology            |
|-----------|------------------------|
| Frontend  | React, TypeScript, Vite, Recharts |
| Backend   | Python, FastAPI       |
| Data      | SMHI API (forecast)   |
| Geocoding | Nominatim (OSM)       |
| ML        | PyTorch               |
| IaC       | Terraform             |
| CI/CD     | GitHub Actions        |

## Quick Start

### Backend

```bash

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install fastapi "uvicorn[standard]"
python -m pip install -U pip
python -m pip install -r requirements.txt (or directly ``` pip install -r requirements.txt ```)
cd backend
uvicorn app:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. The frontend proxies `/api` to the backend.

### Optional: Train ML Model

```bash
cd backend
python3.11 train_model.py
```

## Project Structure

```
├── backend/          # Python FastAPI app, SMHI client, geocoding, ML model
├── frontend/         # React + TypeScript web app
├── terraform/        # AWS deployment (ECR, S3)
├── .github/workflows/  # GitHub Actions CI/CD
└── technical-report.md  # Detailed architecture
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/search?q=...` | Geocode address/location |
| `GET /api/weather?lat=...&lon=...` | Cloud cover & lightning forecast |
| `GET /api/weather/by-address?q=...` | Weather by address string |
| `GET /api/ai-patterns?lat=...&lon=...` | AI atmospheric pattern analysis |

## SMHI Coverage

SMHI provides forecast data for the **Nordic region** (Sweden, Norway, Finland, Denmark, Baltic). Use Nordic coordinates for best results.

## License

MIT
