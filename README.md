# CC Fraud Pipeline 🔍

Détection automatique en temps réel de transactions frauduleuses par carte bancaire.

Projet de certification **Bloc 3 — Concevoir et mettre en œuvre des pipelines de données**
Jedha Bootcamp — Bac+5 Lead Data Science

---

## Architecture

![Architecture](docs/architecture.png)

| Composant | Technologie | Rôle |
|---|---|---|
| Feature engineering | pandas · numpy | haversine, age, hour, day_of_week |
| Modèle | LightGBM | Classification binaire — scale_pos_weight=258 |
| Experiment tracking | MLflow (HF Space) | Runs, métriques, registry |
| Artifact store | AWS S3 | `s3://mlflow-remote-storage/cc-fraud/` |
| Inference API | FastAPI (HF Space) | `cc-fraud-sentinel` — charge `@champion` |
| Message broker | Redpanda Cloud | Topic `payments.raw` — free tier |
| Consumer ETL | Python · kafka-python | Enrich → predict → insert NeonDB |
| Base de données | NeonDB / Postgres | Table `transactions` |
| Alertes temps réel | Slack webhook | Notification immédiate si fraude |
| Orchestration batch | Prefect Cloud Hobby | Flow quotidien cron `0 6 * * *` |
| Dashboard | Streamlit (HF Space) | Rapport J-1 |

---

## Dataset

**fraudTest.csv** — 555 719 transactions bancaires synthétiques

| Stat | Valeur |
|---|---|
| Transactions | 555 719 |
| Features | 23 colonnes |
| Fraudes | 2 145 (0.39%) |
| Légitimes | 553 574 |
| Déséquilibre | 1:258 |

Target : `is_fraud` — déséquilibre géré via `scale_pos_weight=258`

---

## Performances du modèle

| Métrique | Valeur |
|---|---|
| ROC-AUC | 0.9780 |
| PR-AUC | 0.8858 |
| F1 (fraude) | 0.7498 |
| Recall | 0.8834 |
| Precision | 0.6512 |

Le Recall élevé (88%) est la priorité métier — mieux vaut quelques fausses alertes que rater une vraie fraude.

---

## Structure du projet

```
cc-fraud-pipeline/
│
├── data/
│   └── .gitkeep                    # fraudTest.csv ici — ignoré par git
│
├── docs/
│   └── architecture.png            # schéma d'architecture
│
├── notebooks/
│   └── 01_eda_training.ipynb
│
├── src/
│   ├── __init__.py
│   ├── config.py                   # constantes partagées
│   ├── preprocessing.py            # feature engineering
│   ├── train.py                    # entraînement + MLflow
│   │
│   ├── mlflow_utils/
│   │   ├── __init__.py
│   │   ├── tracking.py             # init expérience cc-fraud-detection
│   │   └── registry.py             # promote @champion · load model
│   │
│   ├── api/                        # source de vérité FastAPI
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── requirements.txt
│   │
│   ├── streaming/
│   │   ├── __init__.py
│   │   ├── producer.py             # simule API paiements · 80/20
│   │   └── consumer.py             # ETL : Kafka → FastAPI → NeonDB
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── schema.sql              # CREATE TABLE transactions
│   │   └── client.py              # insert · fetch_yesterday_summary
│   │
│   ├── alerts/
│   │   ├── __init__.py
│   │   └── notify.py              # Slack webhook temps réel
│   │
│   ├── orchestration/
│   │   ├── __init__.py
│   │   └── daily_pipeline.py      # Prefect flow · cron 06:00
│   │
│   └── report/
│       ├── __init__.py
│       └── dashboard.py           # Streamlit · SQLAlchemy · NeonDB
│
├── tests/
│   ├── test_preprocessing.py
│   ├── test_consumer.py
│   └── test_db.py
│
├── .env.example
├── .env                            # ignoré par git
├── .gitignore
├── requirements.txt
├── Makefile
└── README.md

# Repo HF séparé — au même niveau que cc-fraud-pipeline/
../cc-fraud-sentinel/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── schemas.py
│   ├── config.py
│   └── preprocessing.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Installation

```bash
git clone https://github.com/VoxUp/cc-fraud-pipeline
cd cc-fraud-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copier et renseigner les variables d'environnement :

```bash
cp .env.example .env
```

### Variables requises

```bash
# ── Redpanda / Kafka ─────────────────────────────────────
REDPANDA_BOOTSTRAP=seed-xxx.xxx.redpanda.com:9092
REDPANDA_USERNAME=ccfraud-user
REDPANDA_PASSWORD=your-password
REDPANDA_TOPIC=payments.raw

# ── NeonDB ───────────────────────────────────────────────
DATABASE_URL=postgresql://user:password@ep-xxx.eu-west-2.aws.neon.tech/neondb?sslmode=require

# ── MLflow ───────────────────────────────────────────────
# Serveur partagé avec IDNet — expérience distincte cc-fraud-detection
MLFLOW_TRACKING_URI=https://VoxUp.hf.space
MLFLOW_TRACKING_USERNAME=user
MLFLOW_TRACKING_PASSWORD=password

# ── AWS S3 ───────────────────────────────────────────────
# Bucket partagé — préfixe dédié s3://.../cc-fraud/
AWS_ACCESS_KEY_ID=key
AWS_SECRET_ACCESS_KEY=secret
AWS_DEFAULT_REGION=region

# ── Prefect ──────────────────────────────────────────────
PREFECT_API_KEY=-prefect-api-key
PREFECT_API_URL=https://api.prefect.cloud/api/accounts/<account-id>/workspaces/<workspace-id>

# ── CC Fraud API ─────────────────────────────────────────
CC_FRAUD_API_URL=https://VoxUp-cc-fraud-sentinel.hf.space/predict

# ── Alertes ──────────────────────────────────────────────
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
```

---

## Lancer le pipeline

### 1. Entraînement

```bash
make train
```

Promouvoir le modèle en `@champion` :

```bash
python -c "from src.mlflow_utils.registry import promote_champion; promote_champion()"
```

### 2. Initialiser la base de données

```bash
python -c "
import psycopg2
from src.config import DATABASE_URL
with psycopg2.connect(DATABASE_URL) as conn:
    with conn.cursor() as cur:
        with open('src/db/schema.sql') as f:
            cur.execute(f.read())
    conn.commit()
    print('Table transactions créée.')
"
```

### 3. Déployer l'API

```bash
make deploy-api
```

Synchronise `src/api/` vers `../cc-fraud-sentinel/` et push sur HF Space.

API disponible sur : `https://VoxUp-cc-fraud-sentinel.hf.space`
Docs Swagger : `https://VoxUp-cc-fraud-sentinel.hf.space/docs`

### 4. Connexion Prefect Cloud

```bash
prefect cloud login --key -prefect-api-key
```

### 5. Lancer le pipeline complet — 4 terminaux

```bash
# Terminal 1 — Orchestration Prefect (batch quotidien cron 06:00)
make orchestrate

# Terminal 2 — Consumer ETL (écoute Kafka en continu)
make consume

# Terminal 3 — Producer (simule les paiements)
make produce

# Terminal 4 — Dashboard Streamlit
make report
```

### 6. Déclencher le batch manuellement (démo / test)

```bash
prefect deployment run 'cc-fraud-daily-pipeline/cc-fraud-daily-deployment'
```

> **Note** : `make orchestrate` utilise Prefect `.serve()` — le worker tourne
> en local et doit être actif pour que le cron se déclenche à 06:00.
> Pour un déclenchement manuel hors cron, utiliser la commande ci-dessus.

---

## Services déployés

| Service | URL |
|---|---|
| Inference API | `https://VoxUp-cc-fraud-sentinel.hf.space` |
| API Docs | `https://VoxUp-cc-fraud-sentinel.hf.space/docs` |
| MLflow UI | `https://VoxUp-mlflow-server.hf.space` |
| Prefect Cloud | `https://app.prefect.cloud` |

---

## Objectifs business

| Objectif | Solution |
|---|---|
| Notification immédiate si fraude détectée | Consumer → `notify.py` → Slack `#fraud-alerts` |
| Rapport quotidien des transactions J-1 | Prefect cron `0 6 * * *` → Streamlit dashboard |

---

## Commandes disponibles

```bash
make install      # pip install -r requirements.txt
make train        # entraînement + log MLflow
make produce      # simule 100 transactions Kafka
make consume      # consumer ETL en continu
make orchestrate  # Prefect worker + deployment cron 06:00
make report       # Streamlit dashboard
make deploy-api   # sync + push cc-fraud-sentinel HF Space
make test         # pytest tests/
```

---

## Séparation IDNet / CC-Fraud

Ce projet partage le serveur MLflow et le bucket S3 avec le projet IDNet (Bloc 4) :

| Ressource | IDNet (Bloc 4) | CC Fraud (Bloc 3) |
|---|---|---|
| MLflow experiment | `idnet-fraud-detection` | `cc-fraud-detection` |
| Registered model | `IDNet-Fraud-Detector` | `CreditCard-Fraud-Detector` |
| S3 prefix | `s3://.../idnet/` | `s3://.../cc-fraud/` |
| HF Space API | `Id-Fraud-Sentinel` | `cc-fraud-sentinel` |
| NeonDB | base `idnet` | base `neondb` |

---

## Améliorations possibles

- **Airflow sur HF Space** — orchestration cloud autonome sans dépendance machine locale
- **Tuning du seuil** `FRAUD_THRESHOLD` via courbe Precision-Recall
- **Feature store** — centraliser le preprocessing pour producer et API
- **Tests d'intégration** consumer → API → DB
- **Monitoring drift** — détecter la dérive du modèle sur les données réelles
- **SMOTE** — oversampling sur train set pour améliorer la Precision

---

## Auteur

Ibrahim BAH — Jedha Bootcamp  Lead Data Science — Bloc 3