import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _get_env_str(name: str, default: str) -> str:
    return os.getenv(name, default)


def _get_env_bool(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


DATA_PATH = _get_env_str("DATA_PATH", str(PROJECT_ROOT / "data" / "players.csv"))
MODEL_PATH = _get_env_str("MODEL_PATH", str(PROJECT_ROOT / "models" / "churn_model.pkl"))
CHROMA_PATH = _get_env_str("CHROMA_PATH", str(PROJECT_ROOT / "rag" / "chroma_db"))

API_BASE_URL = _get_env_str("API_BASE_URL", "http://127.0.0.1:8000")
API_HOST = _get_env_str("API_HOST", "0.0.0.0")
API_PORT = int(_get_env_str("API_PORT", "8000"))

STREAMLIT_HOST = _get_env_str("STREAMLIT_HOST", "0.0.0.0")
STREAMLIT_PORT = int(_get_env_str("STREAMLIT_PORT", "8501"))

AWS_REGION = _get_env_str("AWS_REGION", "eu-west-2")
S3_BUCKET = _get_env_str("S3_BUCKET", "player-intelligence-data")
S3_KEY = _get_env_str("S3_KEY", "datasets/players.csv")
S3_FALLBACK_TO_LOCAL = _get_env_bool("S3_FALLBACK_TO_LOCAL", True)
