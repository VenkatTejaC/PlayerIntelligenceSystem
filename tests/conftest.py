from pathlib import Path
import sys

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_PATH = PROJECT_ROOT / "data" / "players.csv"


@pytest.fixture(scope="session")
def players_df() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH)


@pytest.fixture
def sample_df(players_df: pd.DataFrame) -> pd.DataFrame:
    # Small copy keeps tests fast and avoids cross-test mutation.
    return players_df.head(50).copy()
