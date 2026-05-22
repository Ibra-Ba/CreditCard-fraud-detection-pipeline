import mlflow
from prefect import flow, task, get_run_logger
from datetime import datetime, timedelta

from src.config import (
    MLFLOW_TRACKING_URI,
    EXPERIMENT_NAME,
    DATABASE_URL,
)
from src.db.client import fetch_yesterday_summary, fetch_recent_frauds
from src.alerts.notify import send_alert


# ── Tasks ────────────────────────────────────────────────

@task(name="extract-yesterday-transactions", retries=2, retry_delay_seconds=30)
def extract() -> dict:
    logger = get_run_logger()
    logger.info("Extraction des transactions J-1...")
    summary = fetch_yesterday_summary()
    logger.info(f"Transactions : {summary['total_transactions']}")
    logger.info(f"Fraudes      : {summary.get('total_frauds', 0)}")
    logger.info(f"Taux fraude  : {summary['fraud_rate_pct']}%")
    return summary


@task(name="extract-recent-frauds", retries=2, retry_delay_seconds=30)
def extract_frauds() -> list:
    logger = get_run_logger()
    frauds = fetch_recent_frauds(limit=50)
    logger.info(f"{len(frauds)} fraudes récentes récupérées")
    return frauds


#@task(name="log-metrics-mlflow")
#def log_to_mlflow(summary: dict) -> None:
#    logger = get_run_logger()
#    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI) # type: ignore
#    mlflow.set_experiment(EXPERIMENT_NAME)

#    with mlflow.start_run(run_name=f"ccfraud_daily_{datetime.now().strftime('%Y%m%d')}"):
 #       mlflow.log_metrics({
 #           "daily_total_transactions": float(summary["total_transactions"]),
 #           "daily_total_frauds":       float(summary["total_frauds"]),
 #           "daily_fraud_rate_pct":     float(summary["fraud_rate_pct"] or 0),
 #           "daily_avg_amount":         float(summary["avg_amount"] or 0),
  #          "daily_fraud_amount":       float(summary["fraud_amount"] or 0),
 #       })
 #   logger.info("Métriques loggées dans MLflow")

@task(name="log-metrics-mlflow")
def log_to_mlflow(summary: dict) -> None:
    logger = get_run_logger()
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name=f"ccfraud_daily_{datetime.now().strftime('%Y%m%d')}"):
        mlflow.log_metrics({
            "daily_total_transactions": float(summary.get("total_transactions") or 0),
            "daily_total_frauds":       float(summary.get("total_frauds") or 0),
            "daily_fraud_rate_pct":     float(summary.get("fraud_rate_pct") or 0),
            "daily_avg_amount":         float(summary.get("avg_amount") or 0),
            "daily_fraud_amount":       float(summary.get("fraud_amount") or 0),
        })
    logger.info("Métriques loggées dans MLflow")


@task(name="send-daily-summary-alert")
def notify_summary(summary: dict) -> None:
    logger = get_run_logger()
    from src.config import SLACK_WEBHOOK_URL
    import requests

    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL non configuré — résumé ignoré")
        return

    message = (
        f":bar_chart: *Rapport quotidien fraudes — {datetime.now().strftime('%d/%m/%Y')}*\n"
        f"• Transactions : *{summary['total_transactions']}*\n"
        f"• Fraudes      : *{summary.get('total_frauds', 0)}*\n"
        f"• Taux         : *{summary['fraud_rate_pct']}%*\n"
        f"• Montant total fraudé : *{summary['fraud_amount']} €*"
    )

    try:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=5)
        logger.info("Résumé quotidien envoyé sur Slack")
    except Exception as e:
        logger.warning(f"Échec envoi Slack : {e}")


# ── Flow ─────────────────────────────────────────────────

@flow(
    name="cc-fraud-daily-pipeline",
    description="Batch quotidien — agrégation J-1, log MLflow, alerte Slack",
)
def daily_pipeline() -> None:
    logger = get_run_logger()
    logger.info("Démarrage du pipeline quotidien cc-fraud")

    # extract
    summary = extract()
    frauds  = extract_frauds()

    # log MLflow
    log_to_mlflow(summary)

    # notify
    notify_summary(summary)

    logger.info("Pipeline quotidien terminé.")


# ── Deployment ───────────────────────────────────────────

if __name__ == "__main__":
    daily_pipeline.serve(
        name="cc-fraud-daily-deployment",
        cron="0 6 * * *",
    )