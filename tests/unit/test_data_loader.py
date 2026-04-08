import pandas as pd
import pytest
from botocore.exceptions import ClientError

from utils import data_loader


class FakeS3Body:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def read(self) -> bytes:
        return self._content


class FakeS3Client:
    def __init__(self, content: bytes) -> None:
        self._content = content

    def get_object(self, Bucket: str, Key: str) -> dict:
        return {"Body": FakeS3Body(self._content)}


class FakeSession:
    def __init__(self, *, content: bytes) -> None:
        self._content = content

    def client(self, service_name: str) -> FakeS3Client:
        assert service_name == "s3"
        return FakeS3Client(self._content)


@pytest.mark.unit
def test_get_aws_profile_prefers_environment(monkeypatch):
    monkeypatch.setenv("AWS_PROFILE", "sso-dev")

    assert data_loader.get_aws_profile("default") == "sso-dev"


@pytest.mark.unit
def test_create_s3_session_uses_default_chain_for_default_profile(monkeypatch):
    calls = []

    def fake_session(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.delenv("AWS_PROFILE", raising=False)
    monkeypatch.setattr(data_loader.boto3, "Session", fake_session)

    data_loader.create_s3_session(region="eu-west-2", profile="default")

    assert calls == [{"region_name": "eu-west-2"}]


@pytest.mark.unit
def test_read_s3_players_data_reads_csv_from_s3(monkeypatch):
    csv_bytes = b"player_id,sessions_per_week,avg_session_time,spend,days_since_last_login,churn\n1,3,45,9.99,2,0\n"

    monkeypatch.setattr(
        data_loader,
        "create_s3_session",
        lambda region, profile: FakeSession(content=csv_bytes),
    )

    df = data_loader.read_s3_players_data()
    source = data_loader.get_current_data_source()

    assert list(df.columns) == [
        "player_id",
        "sessions_per_week",
        "avg_session_time",
        "spend",
        "days_since_last_login",
        "churn",
    ]
    assert int(df.iloc[0]["player_id"]) == 1
    assert source["source"] == "s3"
    assert source["location"] == "s3://player-intelligence-data/datasets/players.csv"


@pytest.mark.unit
def test_load_players_data_falls_back_to_local(monkeypatch):
    expected = pd.DataFrame({"player_id": [1]})

    def fake_read_s3_players_data(**kwargs):
        raise data_loader.ProfileNotFound(profile="default")

    monkeypatch.setattr(data_loader, "read_s3_players_data", fake_read_s3_players_data)
    monkeypatch.setattr(data_loader, "read_local_players_data", lambda data_path: expected)

    df = data_loader.load_players_data()

    assert df.equals(expected)


@pytest.mark.unit
def test_load_players_data_warns_with_sso_login_hint_for_expired_token(monkeypatch):
    expected = pd.DataFrame({"player_id": [1]})
    expired_token_error = ClientError(
        {"Error": {"Code": "ExpiredToken", "Message": "The provided token has expired."}},
        "GetObject",
    )

    def fake_read_s3_players_data(**kwargs):
        raise expired_token_error

    monkeypatch.setattr(data_loader, "read_s3_players_data", fake_read_s3_players_data)
    monkeypatch.setattr(data_loader, "read_local_players_data", lambda data_path: expected)

    with pytest.warns(UserWarning, match=r"aws sso login"):
        df = data_loader.load_players_data(profile="default")

    assert df.equals(expected)


@pytest.mark.unit
def test_load_players_data_raises_without_fallback(monkeypatch):
    def fake_read_s3_players_data(**kwargs):
        raise data_loader.ProfileNotFound(profile="default")

    monkeypatch.setattr(data_loader, "read_s3_players_data", fake_read_s3_players_data)

    with pytest.raises(data_loader.ProfileNotFound):
        data_loader.load_players_data(fallback_to_local=False)
