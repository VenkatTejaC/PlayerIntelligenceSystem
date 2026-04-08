import pandas as pd
import pytest
import numpy as np

from models.train_churn_model import (
    FEATURE_COLUMNS,
    save_model,
    split_features_target,
    train_model,
)


class DummyModel:
    def __init__(self) -> None:
        self.was_fit = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> "DummyModel":
        self.was_fit = True
        return self

    def predict_proba(self, X: pd.DataFrame):
        return np.array(
            [[0.1, 0.9] if value > 4 else [0.9, 0.1] for value in X["spend"]]
        )


@pytest.mark.unit
def test_split_features_target_returns_expected_columns(players_df):
    X, y = split_features_target(players_df)

    assert list(X.columns) == FEATURE_COLUMNS
    assert y.name == "churn"


@pytest.mark.unit
def test_train_model_returns_fitted_model_and_auc(players_df):
    model, auc = train_model(
        players_df[FEATURE_COLUMNS],
        players_df["churn"],
        model=DummyModel(),
    )

    assert model.was_fit is True
    assert 0.0 <= auc <= 1.0


@pytest.mark.unit
def test_save_model_delegates_to_joblib_dump(monkeypatch):
    calls = []

    def fake_dump(model, model_path):
        calls.append((model, model_path))

    monkeypatch.setattr("models.train_churn_model.joblib.dump", fake_dump)

    model = object()
    save_model(model, "models/test_model.pkl")

    assert calls == [(model, "models/test_model.pkl")]
