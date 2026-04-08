import pandas as pd

from utils.config import DATA_PATH


def clear_players_data_cache() -> None:
    return None


def get_current_data_source() -> dict[str, str]:
    return {
        "source": "local",
        "location": DATA_PATH,
    }


def load_players_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(data_path)
