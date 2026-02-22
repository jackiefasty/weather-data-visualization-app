"""Tests for SMHI API client."""
import pytest
from unittest.mock import patch, MagicMock

from api_client import extract_cloud_cover_and_lightning, get_forecast_for_location


def test_extract_cloud_cover_and_lightning():
    """Test extraction of cloud cover and lightning from SMHI response."""
    data = {
        "timeSeries": [
            {
                "validTime": "2026-02-22T18:00:00Z",
                "parameters": [
                    {"name": "tcc_mean", "values": [8]},
                    {"name": "tstm", "values": [15]},
                ],
            },
            {
                "validTime": "2026-02-22T19:00:00Z",
                "parameters": [
                    {"name": "tcc_mean", "values": [4]},
                    {"name": "tstm", "values": [-9]},
                ],
            },
        ]
    }
    result = extract_cloud_cover_and_lightning(data)
    assert len(result) == 2
    assert result[0]["cloud_cover_pct"] == 100.0  # 8/8 octas
    assert result[0]["lightning_prob_pct"] == 15
    assert result[1]["cloud_cover_pct"] == 50.0   # 4/8 octas
    assert result[1]["lightning_prob_pct"] == 0   # -9 -> 0


@patch("api_client.call_smhi_forecast_api")
def test_get_forecast_for_location(mock_call):
    """Test get_forecast_for_location with mocked API."""
    mock_call.return_value = {
        "approvedTime": "2026-02-22T17:00:00Z",
        "referenceTime": "2026-02-22T17:00:00Z",
        "geometry": {"type": "Point", "coordinates": [[16.0, 58.0]]},
        "timeSeries": [
            {
                "validTime": "2026-02-22T18:00:00Z",
                "parameters": [
                    {"name": "tcc_mean", "values": [4]},
                    {"name": "tstm", "values": [0]},
                ],
            },
        ],
    }
    result = get_forecast_for_location(16.0, 58.0)
    mock_call.assert_called_once_with(16.0, 58.0)
    assert "time_series" in result
    assert len(result["time_series"]) == 1
    assert result["longitude"] == 16.0
    assert result["latitude"] == 58.0
