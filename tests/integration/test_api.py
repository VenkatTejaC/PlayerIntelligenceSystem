from fastapi.testclient import TestClient
import pytest

from backend.api import app

client = TestClient(app)


@pytest.mark.integration
def test_health_endpoint_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["player_count"] > 0
    assert payload["data_source"] == "local"
    assert payload["data_location"] == "data/players.csv"


@pytest.mark.integration
def test_debug_data_source_endpoint_returns_source_details() -> None:
    response = client.get("/debug/data-source")

    assert response.status_code == 200
    payload = response.json()
    assert payload["source"] == "local"
    assert payload["location"] == "data/players.csv"


@pytest.mark.integration
def test_reload_data_source_endpoint_reloads_data() -> None:
    response = client.post("/debug/reload-data")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "reloaded"
    assert payload["player_count"] > 0
    assert payload["data_source"] == "local"
    assert payload["data_location"] == "data/players.csv"


@pytest.mark.integration
def test_players_endpoint_returns_player_ids() -> None:
    response = client.get("/players")

    assert response.status_code == 200
    payload = response.json()
    assert payload["player_count"] > 0
    assert 0 in payload["player_ids"]
    assert payload["data_source"] == "local"


@pytest.mark.integration
def test_player_analysis_endpoint_returns_recommendation() -> None:
    response = client.get("/players/25")

    assert response.status_code == 200
    payload = response.json()
    assert payload["player"]["player_id"] == 25
    assert "recommendation" in payload["player"]
    assert payload["data_source"] == "local"


@pytest.mark.integration
def test_player_analysis_endpoint_returns_404_for_missing_player() -> None:
    response = client.get("/players/1000000")

    assert response.status_code == 404
