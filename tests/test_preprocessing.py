import pandas as pd
import pytest
from src.preprocessing import haversine, engineer_features, payload_to_features


SAMPLE_ROW = {
    "trans_date_trans_time": "2020-06-21 12:14:25",
    "lat": 36.0788, "long": -81.1781,
    "merch_lat": 36.011293, "merch_long": -81.926843,
    "dob": "1968-03-19",
    "amt": 149.5,
    "category": "shopping_net",
    "gender": "F",
    "city_pop": 3495,
}


def test_haversine_returns_positive():
    d = haversine(48.8566, 2.3522, 51.5074, -0.1278)  # Paris → London
    assert d > 0
    assert round(d) == 341


def test_engineer_features_columns():
    df = pd.DataFrame([SAMPLE_ROW])
    result = engineer_features(df)
    for col in ["hour", "day_of_week", "age", "distance_km"]:
        assert col in result.columns


def test_engineer_features_age_positive():
    df = pd.DataFrame([SAMPLE_ROW])
    result = engineer_features(df)
    assert result["age"].iloc[0] > 0


def test_payload_to_features_shape():
    result = payload_to_features(SAMPLE_ROW)
    assert result.shape == (1, 8)   # 6 num + 2 cat


def test_payload_to_features_no_leakage():
    result = payload_to_features(SAMPLE_ROW)
    # colonnes brutes ne doivent pas apparaître
    for col in ["lat", "long", "dob", "trans_date_trans_time"]:
        assert col not in result.columns