import os
from dotenv import load_dotenv

load_dotenv()

# ── Kafka ────────────────────────────────────────────────
KAFKA_TOPIC     = os.getenv("REDPANDA_TOPIC", "payments.raw")
KAFKA_BOOTSTRAP = os.getenv("REDPANDA_BOOTSTRAP")
KAFKA_USERNAME  = os.getenv("REDPANDA_USERNAME")
KAFKA_PASSWORD  = os.getenv("REDPANDA_PASSWORD")
KAFKA_GROUP_ID  = "fraud-detector-group"

# ── MLflow ───────────────────────────────────────────────
MLFLOW_TRACKING_URI   = os.getenv("MLFLOW_TRACKING_URI")
EXPERIMENT_NAME       = "cc-fraud-detection"
REGISTERED_MODEL_NAME = "CreditCard-Fraud-Detector"
MODEL_ALIAS           = "champion"
RUN_NAME_PREFIX       = "ccfraud"
S3_ARTIFACT_PREFIX    = "s3://mlflow-remote-storage/cc-fraud/"

# ── Features ─────────────────────────────────────────────
FEATURES_NUM = ["amt", "distance_km", "age", "hour", "day_of_week", "city_pop"]
FEATURES_CAT = ["category", "gender"]
FEATURES_ALL = FEATURES_NUM + FEATURES_CAT
TARGET       = "is_fraud"

# ── Seuil de détection ───────────────────────────────────
FRAUD_THRESHOLD = 0.5

# ── DB ───────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL")

# ── Prefect ──────────────────────────────────────────────
PREFECT_API_KEY = os.getenv("PREFECT_API_KEY")
PREFECT_API_URL = os.getenv("PREFECT_API_URL")

# ── Alertes ──────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")