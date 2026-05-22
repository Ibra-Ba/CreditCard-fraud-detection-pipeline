import json
import os
import requests
from kafka import KafkaConsumer
from dotenv import load_dotenv
from src.config import (
    KAFKA_BOOTSTRAP,
    KAFKA_USERNAME,
    KAFKA_PASSWORD,
    KAFKA_TOPIC,
    KAFKA_GROUP_ID,
    FRAUD_THRESHOLD,
)
from src.db.client import insert_transaction
from src.alerts.notify import send_alert

load_dotenv()

# ── API endpoint ─────────────────────────────────────────

API_URL = os.getenv(
    "CC_FRAUD_API_URL",
    "https://<username>-cc-fraud-sentinel.hf.space/predict"
)


# ── Kafka consumer ───────────────────────────────────────

def build_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-256",
        sasl_plain_username=KAFKA_USERNAME,
        sasl_plain_password=KAFKA_PASSWORD,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id=KAFKA_GROUP_ID,
    )


# ── Appel API inference ──────────────────────────────────

def call_predict(payload: dict) -> dict:
    """Appelle le endpoint /predict et retourne la prédiction."""
    body = {
        "trans_num":             payload["trans_num"],
        "amt":                   payload["amt"],
        "category":              payload["category"],
        "gender":                payload["gender"],
        "city_pop":              payload["city_pop"],
        "lat":                   payload["lat"],
        "long":                  payload["long"],
        "merch_lat":             payload["merch_lat"],
        "merch_long":            payload["merch_long"],
        "dob":                   payload["dob"],
        "trans_date_trans_time": payload["trans_date_trans_time"],
    }
    response = requests.post(API_URL, json=body, timeout=10)
    response.raise_for_status()
    return response.json()


# ── Main loop ────────────────────────────────────────────

def consume() -> None:
    consumer = build_consumer()
    print(f"Consumer démarré — écoute '{KAFKA_TOPIC}'...")

    for message in consumer:
        payload    = message.value
        trans_num  = payload["trans_num"]

        try:
            prediction = call_predict(payload)
            is_fraud   = prediction["is_fraud"]
            score      = prediction["fraud_score"]

            # enrichit le payload avec la prédiction
            record = {**payload, "is_fraud_pred": is_fraud, "fraud_score": score}

            # stockage NeonDB
            insert_transaction(record)

            label = "🔴 FRAUD" if is_fraud else "🟢 legit"
            print(f"[{label}] {trans_num} | score={score} | amt={payload['amt']}")

            # alerte temps réel si fraude détectée
            if is_fraud:
                send_alert(record)

        except Exception as e:
            print(f"[ERROR] {trans_num} : {e}")
            continue


if __name__ == "__main__":
    consume()