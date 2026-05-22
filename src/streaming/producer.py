import json
import time
import os
import pandas as pd
from kafka import KafkaProducer
from dotenv import load_dotenv
from src.config import (
    KAFKA_BOOTSTRAP,
    KAFKA_USERNAME,
    KAFKA_PASSWORD,
    KAFKA_TOPIC,
)

load_dotenv()


# ── Kafka producer ───────────────────────────────────────

def build_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        security_protocol="SASL_SSL",
        sasl_mechanism="SCRAM-SHA-256",
        sasl_plain_username=KAFKA_USERNAME,
        sasl_plain_password=KAFKA_PASSWORD,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )


# ── Payload builder ──────────────────────────────────────

def row_to_payload(row: pd.Series) -> dict:
    """Extrait les colonnes brutes nécessaires depuis une ligne du CSV."""
    return {
        "trans_num":             row["trans_num"],
        "cc_num":                str(row["cc_num"]),
        "amt":                   row["amt"],
        "category":              row["category"],
        "gender":                row["gender"],
        "lat":                   row["lat"],
        "long":                  row["long"],
        "merch_lat":             row["merch_lat"],
        "merch_long":            row["merch_long"],
        "city_pop":              row["city_pop"],
        "dob":                   row["dob"],
        "trans_date_trans_time": row["trans_date_trans_time"],
        # label réel — utile pour évaluation, non utilisé par l'API
        "is_fraud_actual":       int(row["is_fraud"]),
    }


# ── Main ─────────────────────────────────────────────────

def produce(n: int = 100, delay: float = 0.5) -> None:
    """
    Envoie n transactions dans le topic Kafka.
    Stratégie : 80% légitimes + 20% frauduleuses pour la démo.
    """
    df = pd.read_csv("data/fraudTest.csv")

    legit  = df[df["is_fraud"] == 0].sample(int(n * 0.8), random_state=42)
    fraud  = df[df["is_fraud"] == 1].sample(int(n * 0.2), random_state=42)
    sample = pd.concat([legit, fraud]).sample(frac=1, random_state=42)

    producer = build_producer()
    print(f"Envoi de {len(sample)} transactions vers '{KAFKA_TOPIC}'...")

    for _, row in sample.iterrows():
        payload = row_to_payload(row)
        producer.send(KAFKA_TOPIC, value=payload)
        label = "🔴 FRAUD" if payload["is_fraud_actual"] else "🟢 legit"
        print(f"[{label}] {payload['trans_num']} | amt={payload['amt']}")
        time.sleep(delay)

    producer.flush()
    print("Done.")


if __name__ == "__main__":
    produce()