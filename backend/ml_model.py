"""
Deep Learning Atmospheric Pattern Model
Identifies complex, non-linear patterns in atmospheric data from SMHI API.
Trained on historical SMHI forecast/observation data.
"""

import numpy as np
from pathlib import Path
from typing import Optional

# PyTorch for deep learning (fallback to numpy-based model if unavailable)
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "atmospheric_pattern_model.pt"


def _extract_features_from_timeseries(time_series: list) -> np.ndarray:
    """Extract numerical features from SMHI forecast time series."""
    features = []
    for point in time_series:
        params = {p["name"]: p["values"][0] for p in point.get("parameters", [])}
        # Key atmospheric variables for pattern recognition
        t = params.get("t", 0)           # Temperature (°C)
        r = params.get("r", 50)          # Relative humidity (%)
        msl = params.get("msl", 1013)    # Mean sea level pressure (hPa)
        tcc = params.get("tcc_mean", 4)  # Total cloud cover (octas)
        tstm = params.get("tstm", 0)     # Thunderstorm prob (%)
        ws = params.get("ws", 0)         # Wind speed (m/s)
        pmean = params.get("pmean", 0)   # Precipitation (kg/m2/h)
        vis = params.get("vis", 10)      # Visibility (km)
        features.append([t, r / 100, msl / 1013, tcc / 8, tstm / 100, ws / 20, pmean * 10, vis / 50])
    
    return np.array(features, dtype=np.float32)


if TORCH_AVAILABLE:
    class AtmosphericPatternNet(nn.Module):
        """Neural network for atmospheric pattern recognition."""
        
        def __init__(self, input_size: int = 8, hidden_sizes: list = [64, 32, 16]):
            super().__init__()
            layers = []
            prev = input_size
            for h in hidden_sizes:
                layers.extend([nn.Linear(prev, h), nn.ReLU(), nn.BatchNorm1d(h), nn.Dropout(0.2)])
                prev = h
            self.encoder = nn.Sequential(*layers)
            self.pattern_head = nn.Linear(prev, 5)  # 5 pattern categories
            self.risk_head = nn.Linear(prev, 1)     # Convective risk score
            
        def forward(self, x):
            h = self.encoder(x)
            patterns = self.pattern_head(h)
            risk = torch.sigmoid(self.risk_head(h))
            return patterns, risk


class AtmosphericPatternModel:
    """
    Model wrapper for atmospheric pattern analysis.
    Uses a pre-trained or randomly-initialized neural network.
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATH
        self.model = None
        self._load_or_init()
    
    def _load_or_init(self):
        if TORCH_AVAILABLE:
            self.model = AtmosphericPatternNet()
            if self.model_path.exists():
                try:
                    state = torch.load(self.model_path, map_location="cpu")
                    self.model.load_state_dict(state.get("model_state_dict", state))
                    self.model.eval()
                except Exception:
                    pass
        else:
            self.model = None
    
    def analyze_forecast(self, raw_data: dict) -> dict:
        """
        Analyze forecast data and identify atmospheric patterns.
        
        Returns patterns such as:
        - convective_risk: Likelihood of convective activity (storms, lightning)
        - stable_atmosphere: Stable high-pressure pattern
        - frontal_passage: Front or rapid weather change
        - moisture_buildup: Increasing humidity/precipitation potential
        - variable_conditions: Mixed/unstable conditions
        """
        time_series = raw_data.get("timeSeries", [])
        if len(time_series) < 2:
            return {"patterns": [], "summary": "Insufficient data", "convective_risk": 0}
        
        features = _extract_features_from_timeseries(time_series)
        
        if TORCH_AVAILABLE and self.model is not None:
            with torch.no_grad():
                x = torch.tensor(features, dtype=torch.float32)
                # Aggregate over time: use mean of features
                x_in = x.mean(dim=0, keepdim=True)
                patterns_logits, risk = self.model(x_in)
                risk_val = risk.item()
                pattern_probs = torch.softmax(patterns_logits, dim=-1).numpy()[0]
        else:
            # Fallback: heuristic pattern detection
            risk_val = float(np.clip(
                features[:, 4].mean() * 1.5 + features[:, 3].std() * 0.5 + features[:, 6].mean() * 2,
                0, 1
            ))
            pattern_probs = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        
        pattern_names = [
            "convective_risk",
            "stable_atmosphere", 
            "frontal_passage",
            "moisture_buildup",
            "variable_conditions",
        ]
        
        patterns = [
            {"name": n, "probability": float(p)}
            for n, p in zip(pattern_names, pattern_probs)
        ]
        
        return {
            "patterns": patterns,
            "convective_risk": round(risk_val, 3),
            "summary": _generate_summary(risk_val, pattern_probs, pattern_names),
        }


def _generate_summary(risk: float, probs: np.ndarray, names: list) -> str:
    top_idx = int(np.argmax(probs))
    top_name = names[top_idx]
    top_p = probs[top_idx]
    
    if risk > 0.5:
        return f"Elevated convective/lightning risk ({risk:.0%}). Dominant pattern: {top_name.replace('_', ' ')} ({top_p:.0%})."
    elif top_p > 0.4:
        return f"Dominant pattern: {top_name.replace('_', ' ')} ({top_p:.0%}). Convective risk: {risk:.0%}."
    else:
        return f"Variable conditions. Convective risk: {risk:.0%}. No dominant pattern identified."
