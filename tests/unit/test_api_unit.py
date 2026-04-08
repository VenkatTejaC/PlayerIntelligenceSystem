import pandas as pd
import pytest

from backend import api


@pytest.mark.unit
def test_debug_data_source_returns_mocked_source(monkeypatch):
    monkeypatch.setattr(api, "load_players", lambda: pd.DataFrame({"player_id": [1]}))
    monkeypatch.setattr(
        api,
        "get_current_data_source",
        lambda: {"source": "local", "location": "data/players.csv"},
    )

    payload = api.debug_data_source()

    assert payload["source"] == "local"
    assert payload["location"] == "data/players.csv"


@pytest.mark.unit
def test_reload_data_source_clears_cache_and_returns_new_source(monkeypatch):
    monkeypatch.setattr(api, "clear_players_data_cache", lambda: None)
    monkeypatch.setattr(api, "load_players", lambda: pd.DataFrame({"player_id": [1, 2]}))
    monkeypatch.setattr(
        api,
        "get_current_data_source",
        lambda: {"source": "local", "location": "data/players.csv"},
    )

    payload = api.reload_data_source()

    assert payload["status"] == "reloaded"
    assert payload["player_count"] == 2
    assert payload["data_source"] == "local"
    assert payload["data_location"] == "data/players.csv"


@pytest.mark.unit
def test_get_player_analysis_returns_mocked_player(monkeypatch):
    mocked_df = pd.DataFrame(
        [
            {
                "player_id": 7,
                "sessions_per_week": 3,
                "avg_session_time": 45,
                "spend": 9.99,
                "days_since_last_login": 2,
                "churn_score": 0.8,
                "segment": 1,
                "recommendation": "Offer discount",
            }
        ]
    )

    monkeypatch.setattr(api, "analyze_players", lambda: mocked_df)
    monkeypatch.setattr(api, "get_current_data_source", lambda: {"source": "local", "location": "data/players.csv"})

    payload = api.get_player_analysis(7)

    assert payload["player"]["player_id"] == 7
    assert payload["player"]["recommendation"] == "Offer discount"
    assert payload["data_source"] == "local"


@pytest.mark.unit
def test_get_player_analysis_raises_404_for_missing_mocked_player(monkeypatch):
    monkeypatch.setattr(api, "analyze_players", lambda: pd.DataFrame(columns=["player_id"]))

    with pytest.raises(api.HTTPException) as exc_info:
        api.get_player_analysis(999)

    assert exc_info.value.status_code == 404
