import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    roc_auc_score,
)
from lightgbm import LGBMClassifier

from src.config import (
    EXPERIMENT_NAME,
    FEATURES_CAT,
    FEATURES_NUM,
    REGISTERED_MODEL_NAME,
    RUN_NAME_PREFIX,
)
from src.preprocessing import prepare_dataset


#  ---- Hyperparamètres ----------------------------

PARAMS = {
    "scale_pos_weight": 258,   # 553574 / 2145
    "n_estimators":     300,
    "learning_rate":    0.05,
    "num_leaves":       63,
    "random_state":     42,
    "n_jobs":           1,     # CPU-only
}


# ------ Preprocessor --------------------

def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), FEATURES_NUM),
        ("cat", OrdinalEncoder(
            handle_unknown="use_encoded_value",
            unknown_value=-1
        ), FEATURES_CAT),
    ])


# ------ Pipeline sklearn ---------------------------

def build_pipeline() -> Pipeline:
    return Pipeline([
        ("preprocessor", build_preprocessor()),
        ("classifier",   LGBMClassifier(**PARAMS)),
    ])


# --------------------- Entraînement --------

def train(data_path: str = "data/fraudTest.csv") -> Pipeline:
    # 1. Chargement + feature engineering
    df = pd.read_csv(data_path)
    X, y = prepare_dataset(df)

    # 2. Split stratifié — conserve le ratio 0.39% fraude
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # 3. MLflow
    from src.mlflow_utils.tracking import init_mlflow
    init_mlflow()

    with mlflow.start_run(run_name=f"{RUN_NAME_PREFIX}_lgbm_v1"):

        # entraînement
        pipeline = build_pipeline()
        pipeline.fit(X_train, y_train)

        # évaluation
        y_pred  = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        report   = classification_report(y_test, y_pred, output_dict=True)
        pr_auc   = average_precision_score(y_test, y_proba)
        roc_auc  = roc_auc_score(y_test, y_proba)
        f1_fraud = report["1"]["f1-score"]
        recall   = report["1"]["recall"]
        precision= report["1"]["precision"]

        # log params
        mlflow.log_params(PARAMS)

        # log métriques
        mlflow.log_metrics({
            "pr_auc":    pr_auc,
            "roc_auc":   roc_auc,
            "f1_fraud":  f1_fraud,
            "recall":    recall,
            "precision": precision,
        })

        # log pipeline complet (preprocessing inclus)
        mlflow.sklearn.log_model(
            pipeline,
            artifact_path="fraud-detector",
            registered_model_name=REGISTERED_MODEL_NAME,
        )

        print(f"PR-AUC   : {pr_auc:.4f}")
        print(f"ROC-AUC  : {roc_auc:.4f}")
        print(f"F1 fraud : {f1_fraud:.4f}")
        print(f"Recall   : {recall:.4f}")
        print(f"Precision: {precision:.4f}")

    return pipeline


# -------------- Entrypoint ------------------------

if __name__ == "__main__":
    train()