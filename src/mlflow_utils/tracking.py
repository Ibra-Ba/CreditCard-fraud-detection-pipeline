import mlflow
from src.config import (
    EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
    S3_ARTIFACT_PREFIX,
)


def init_mlflow() -> None:
    """
    Configure le tracking URI et crée l'expérience cc-fraud
    avec son propre préfixe S3 si elle n'existe pas encore.
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        mlflow.create_experiment(
            name=EXPERIMENT_NAME,
            artifact_location=S3_ARTIFACT_PREFIX,
        )
        print(f"Expérience '{EXPERIMENT_NAME}' créée → {S3_ARTIFACT_PREFIX}")
    else:
        print(f"Expérience '{EXPERIMENT_NAME}' existante — réutilisée")

    mlflow.set_experiment(EXPERIMENT_NAME)