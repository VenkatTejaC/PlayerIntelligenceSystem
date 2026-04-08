import pytest

EXPECTED_COLUMNS = [
    "player_id",
    "sessions_per_week",
    "avg_session_time",
    "spend",
    "days_since_last_login",
    "churn",
]


@pytest.mark.integration
def test_players_csv_exists_and_is_non_empty(players_df):
    assert not players_df.empty


@pytest.mark.integration
def test_players_csv_has_expected_columns(players_df):
    assert list(players_df.columns) == EXPECTED_COLUMNS


@pytest.mark.integration
def test_players_csv_has_no_nulls_in_required_columns(players_df):
    assert players_df[EXPECTED_COLUMNS].isnull().sum().sum() == 0
