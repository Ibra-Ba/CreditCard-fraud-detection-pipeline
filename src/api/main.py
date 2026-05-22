import os
import mlflow.sklearn
import pandas as pd
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

from src.api.schemas import TransactionInput, PredictionOutput
from src.config import (
    MLFLOW_TRACKING_URI,
    REGISTERED_MODEL_NAME,
    MODEL_ALIAS,
    FRAUD_THRESHOLD,
)
from src.preprocessing import payload_to_features

load_dotenv()

app = FastAPI(
    title="CC Fraud Detection API",
    description="Inference API — CreditCard-Fraud-Detector @champion",
    version="1.0.0",
)

# ------Chargement du modèle au démarrage -----

pipeline = None

@app.on_event("startup")
def load_model():
    global pipeline
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    model_uri = f"models:/{REGISTERED_MODEL_NAME}@{MODEL_ALIAS}"
    pipeline  = mlflow.sklearn.load_model(model_uri)
    print(f"Modèle chargé : {model_uri}")


# -----Endpoints--------

@app.get("/health")
def health():
    return {"status": "ok", "model": f"{REGISTERED_MODEL_NAME}@{MODEL_ALIAS}"}


@app.post("/predict", response_model=PredictionOutput)
def predict(transaction: TransactionInput):
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Modèle non chargé")

    try:
        payload  = transaction.model_dump()
        features = payload_to_features(payload)
        score    = pipeline.predict_proba(features)[0][1]
        is_fraud = score >= FRAUD_THRESHOLD
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    return PredictionOutput(
        trans_num=transaction.trans_num,
        is_fraud=is_fraud,
        fraud_score=round(float(score), 4),
    )