import pytest

from utils import data_loader


@pytest.mark.unit
def test_load_players_data_reads_project_csv(players_df):
    df = data_loader.load_players_data()

    assert list(df.columns) == list(players_df.columns)
    assert len(df) == len(players_df)


@pytest.mark.unit
def test_get_current_data_source_returns_local_defaults():
    source = data_loader.get_current_data_source()

    assert source["source"] == "local"
    assert source["location"] == "data/players.csv"
