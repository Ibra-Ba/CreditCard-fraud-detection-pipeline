import mlflow.sklearn
from src.config import MLFLOW_TRACKING_URI, REGISTERED_MODEL_NAME, MODEL_ALIAS


def promote_champion(run_id: str) -> None:
    """Assigne l'alias @champion à la dernière version enregistrée."""
    client = mlflow.MlflowClient(tracking_uri=MLFLOW_TRACKING_URI)
    versions = client.get_latest_versions(REGISTERED_MODEL_NAME)
    if not versions:
        raise ValueError(f"Aucune version trouvée pour {REGISTERED_MODEL_NAME}")
    latest = max(versions, key=lambda v: int(v.version))
    client.set_registered_model_alias(
        name=REGISTERED_MODEL_NAME,
        alias=MODEL_ALIAS,
        version=latest.version,
    )
    print(f"@{MODEL_ALIAS} → version {latest.version}")


def load_champion() -> object:
    """Charge le pipeline @champion depuis MLflow."""
    model_uri = f"models:/{REGISTERED_MODEL_NAME}@{MODEL_ALIAS}"
    return mlflow.sklearn.load_model(model_uri)



if __name__ == "__main__":
    #run1_id = "bd22394b059445c887c821553615986f"
    promote_champion(run_id=run1_id)