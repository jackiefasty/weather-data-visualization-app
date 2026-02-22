# Backend Dockerfile - Weather Data Visualization API
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api_client.py .
COPY geocoding.py .
COPY ml_model.py .
COPY app.py .

# Create models directory for ML weights
RUN mkdir -p models

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
