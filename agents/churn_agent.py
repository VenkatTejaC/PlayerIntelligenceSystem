import joblib
from utils.config import MODEL_PATH

model = joblib.load(MODEL_PATH)

FEATURE_COLUMNS = [
    "sessions_per_week",
    "avg_session_time",
    "spend",
    "days_since_last_login"
]

def churn_agent(df):
    features = df[FEATURE_COLUMNS]  # ✅ only use training features
    df["churn_score"] = model.predict_proba(features)[:, 1]
    return df