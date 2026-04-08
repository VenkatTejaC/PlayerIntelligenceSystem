import joblib
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from utils.config import DATA_PATH, MODEL_PATH
from utils.data_loader import load_players_data

TARGET_COLUMN = "churn"
IDENTIFIER_COLUMNS = ["player_id"]
FEATURE_COLUMNS = [
    "sessions_per_week",
    "avg_session_time",
    "spend",
    "days_since_last_login",
]


def load_training_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    return load_players_data(data_path)


def split_features_target(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    X = df.drop(columns=[*IDENTIFIER_COLUMNS, TARGET_COLUMN])
    y = df[TARGET_COLUMN]
    return X, y


def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    *,
    test_size: float = 0.2,
    random_state: int = 42,
    model: XGBClassifier | None = None,
) -> tuple[XGBClassifier, float]:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    fitted_model = model or XGBClassifier(random_state=random_state)
    fitted_model.fit(X_train, y_train)

    preds = fitted_model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, preds)
    return fitted_model, float(auc)


def save_model(model: XGBClassifier, model_path: str = MODEL_PATH) -> None:
    joblib.dump(model, model_path)


def main() -> float:
    df = load_training_data()
    X, y = split_features_target(df)
    model, auc = train_model(X, y)
    save_model(model)
    print("AUC:", auc)
    print("Model saved")
    return auc


if __name__ == "__main__":
    main()
