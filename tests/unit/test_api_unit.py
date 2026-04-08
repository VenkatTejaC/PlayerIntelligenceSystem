import pandas as pd
import pytest

from backend import api


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

    payload = api.get_player_analysis(7)

    assert payload["player"]["player_id"] == 7
    assert payload["player"]["recommendation"] == "Offer discount"


@pytest.mark.unit
def test_get_player_analysis_raises_404_for_missing_mocked_player(monkeypatch):
    monkeypatch.setattr(api, "analyze_players", lambda: pd.DataFrame(columns=["player_id"]))

    with pytest.raises(api.HTTPException) as exc_info:
        api.get_player_analysis(999)

    assert exc_info.value.status_code == 404
