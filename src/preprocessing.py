import numpy as np
import pandas as pd


# --------Constants-------

FEATURES_NUM = ["amt", "distance_km", "age", "hour", "day_of_week", "city_pop"]
FEATURES_CAT = ["category", "gender"]
FEATURES_ALL = FEATURES_NUM + FEATURES_CAT


# ------------- Geo --------------------------------------------------

def haversine(lat1: float, lon1: float,
              lat2: float, lon2: float) -> float:
    """
    Calcule la distance en km entre deux points géographiques.
    Accepte scalaires et Series pandas.
    """
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return R * 2 * np.arcsin(np.sqrt(a))


# ----------Feature engineering ---------------------------------

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applique le feature engineering complet sur un DataFrame brut.
    Retourne un nouveau DataFrame sans modifier l'original.

    Colonnes attendues en entrée :
        trans_date_trans_time, lat, long, merch_lat, merch_long,
        dob, amt, category, gender, city_pop
    """
    df = df.copy()

    # datetime
    df["trans_datetime"] = pd.to_datetime(df["trans_date_trans_time"])
    df["dob"]            = pd.to_datetime(df["dob"])

    # features temporelles
    df["hour"]        = df["trans_datetime"].dt.hour
    df["day_of_week"] = df["trans_datetime"].dt.dayofweek

    # âge en années
    df["age"] = ((df["trans_datetime"] - df["dob"]).dt.days // 365).astype(int)

    # distance client / marchand
    df["distance_km"] = haversine(
        df["lat"], df["long"],
        df["merch_lat"], df["merch_long"]
    )

    return df


# -----------Payload dict --> DataFrame (usage consumer + API) -------------------

def payload_to_features(payload: dict) -> pd.DataFrame:
    """
    Convertit un payload JSON brut (issu du producer Kafka ou de l'API)
    en DataFrame prêt pour pipeline.predict().

    Le payload contient les colonnes brutes — le feature engineering
    est appliqué ici de manière identique à l'entraînement.
    """
    df = pd.DataFrame([payload])
    df = engineer_features(df)
    return df[FEATURES_ALL]


# ------------------ Batch (usage train.py) --------------

def prepare_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """
    Prépare X et y à partir du CSV brut pour l'entraînement.
    """
    from src.config import TARGET

    df = engineer_features(df)
    X  = df[FEATURES_ALL]
    y  = df[TARGET]
    return X, y