"""
Model Training Script
Trains the atmospheric pattern deep learning model on SMHI historical data.
Run this script to train/retrain the model with available data.
"""

import json
import os
from pathlib import Path

# Fetch data from SMHI API for training (example: Nordic locations)
TRAINING_LOCATIONS = [
    (16.0, 58.0),   # Norrköping
    (18.0, 59.3),   # Stockholm
    (13.0, 55.6),   # Malmö
    (11.9, 57.7),   # Gothenburg
]

SCRIPT_DIR = Path(__file__).parent
MODEL_DIR = SCRIPT_DIR / "models"


def fetch_training_data():
    """Fetch forecast data from SMHI API for multiple locations."""
    from api_client import call_smhi_forecast_api
    
    all_data = []
    for lon, lat in TRAINING_LOCATIONS:
        try:
            data = call_smhi_forecast_api(lon, lat)
            all_data.append({"lon": lon, "lat": lat, "data": data})
        except Exception as e:
            print(f"Failed to fetch ({lon}, {lat}): {e}")
    return all_data


def train_model():
    """Train the atmospheric pattern model."""
    try:
        import torch
        import numpy as np
        from torch.utils.data import DataLoader, TensorDataset
        from ml_model import AtmosphericPatternNet, _extract_features_from_timeseries
    except ImportError as e:
        print(f"PyTorch required for training: {e}")
        print("Install with: pip install torch")
        return
    
    MODEL_DIR.mkdir(exist_ok=True)
    
    # Fetch training data
    print("Fetching training data from SMHI API...")
    raw_data_list = fetch_training_data()
    
    if not raw_data_list:
        print("No data fetched. Using synthetic data for demonstration.")
        np.random.seed(42)
        features = np.random.randn(1000, 8).astype(np.float32)
        labels = np.random.randint(0, 5, 1000)
    else:
        all_features = []
        all_labels = []
        for item in raw_data_list:
            ts = item["data"].get("timeSeries", [])
            feats = _extract_features_from_timeseries(ts)
            all_features.append(feats)
            # Derive labels from thunderstorm prob and cloud cover
            labels = np.clip((feats[:, 4] * 2 + feats[:, 3]) * 1.5, 0, 4).astype(int)
            all_labels.append(labels)
        features = np.vstack(all_features)
        labels = np.concatenate(all_labels)
    
    # Create dataloader
    X = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    dataset = TensorDataset(X, y)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # Train model
    model = AtmosphericPatternNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = torch.nn.CrossEntropyLoss()
    risk_criterion = torch.nn.MSELoss()
    
    model.train()

    for epoch in range(50):
        total_loss = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            patterns, risk = model(batch_x)
            
            # Derive a soft risk label from the pattern label (0=convective = high risk)
            risk_label = (batch_y == 0).float().unsqueeze(1) * 0.8 + 0.1
            
            loss = criterion(patterns, batch_y) + risk_criterion(risk, risk_label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/50, Loss: {total_loss/len(loader):.4f}")
    
    # Save model
    torch.save({"model_state_dict": model.state_dict()}, MODEL_DIR / "atmospheric_pattern_model.pt")
    print(f"Model saved to {MODEL_DIR / 'atmospheric_pattern_model.pt'}")


if __name__ == "__main__":
    train_model()
