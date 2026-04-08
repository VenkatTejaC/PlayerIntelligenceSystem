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
    data_loader.clear_players_data_cache()
    csv_bytes = b"player_id,sessions_per_week,avg_session_time,spend,days_since_last_login,churn\n1,3,45,9.99,2,0\n"

    monkeypatch.setattr(
        data_loader,
        "create_s3_session",
        lambda region, profile: FakeSession(content=csv_bytes),
    )

    df = data_loader.read_s3_players_data()

    assert list(df.columns) == [
        "player_id",
        "sessions_per_week",
        "avg_session_time",
        "spend",
        "days_since_last_login",
        "churn",
    ]
    assert int(df.iloc[0]["player_id"]) == 1


@pytest.mark.unit
def test_load_players_data_falls_back_to_local(monkeypatch):
    data_loader.clear_players_data_cache()
    expected = pd.DataFrame({"player_id": [1]})

    def fake_read_s3_players_data(**kwargs):
        raise data_loader.ProfileNotFound(profile="default")

    monkeypatch.setattr(data_loader, "_load_from_s3_and_cache", lambda **kwargs: (_ for _ in ()).throw(data_loader.ProfileNotFound(profile="default")))
    monkeypatch.setattr(data_loader, "read_local_players_data", lambda data_path: expected)

    df = data_loader.load_players_data(metadata_check_interval_seconds=0)

    assert df.equals(expected)
    assert data_loader.get_current_data_source()["source"] == "local"


@pytest.mark.unit
def test_load_players_data_uses_cached_data_within_interval(monkeypatch):
    data_loader.clear_players_data_cache()
    calls = []
    expected = pd.DataFrame({"player_id": [1]})

    def fake_load_from_s3_and_cache(**kwargs):
        calls.append("s3")
        return data_loader._set_cache(expected, source="s3", location="s3://player-intelligence-data/datasets/players.csv", s3_metadata={"etag": "1", "last_modified": "a"})

    monkeypatch.setattr(data_loader, "_load_from_s3_and_cache", fake_load_from_s3_and_cache)

    first = data_loader.load_players_data(metadata_check_interval_seconds=999)
    second = data_loader.load_players_data(metadata_check_interval_seconds=999)

    assert first.equals(expected)
    assert second.equals(expected)
    assert calls == ["s3"]


@pytest.mark.unit
def test_load_players_data_switches_back_to_s3_when_available(monkeypatch):
    data_loader.clear_players_data_cache()
    local_df = pd.DataFrame({"player_id": [1]})
    s3_df = pd.DataFrame({"player_id": [2]})
    outcomes = iter(["fail", "success"])

    def fake_load_from_s3_and_cache(**kwargs):
        outcome = next(outcomes)
        if outcome == "fail":
            raise data_loader.ProfileNotFound(profile="default")
        return data_loader._set_cache(s3_df, source="s3", location="s3://player-intelligence-data/datasets/players.csv", s3_metadata={"etag": "2", "last_modified": "b"})

    monkeypatch.setattr(data_loader, "_load_from_s3_and_cache", fake_load_from_s3_and_cache)
    monkeypatch.setattr(data_loader, "read_local_players_data", lambda data_path: local_df)

    first = data_loader.load_players_data(metadata_check_interval_seconds=0)
    second = data_loader.load_players_data(metadata_check_interval_seconds=0)

    assert first.equals(local_df)
    assert second.equals(s3_df)
    assert data_loader.get_current_data_source()["source"] == "s3"


@pytest.mark.unit
def test_load_players_data_warns_with_sso_login_hint_for_expired_token(monkeypatch):
    data_loader.clear_players_data_cache()
    expected = pd.DataFrame({"player_id": [1]})
    expired_token_error = ClientError(
        {"Error": {"Code": "ExpiredToken", "Message": "The provided token has expired."}},
        "GetObject",
    )

    monkeypatch.setattr(data_loader, "_load_from_s3_and_cache", lambda **kwargs: (_ for _ in ()).throw(expired_token_error))
    monkeypatch.setattr(data_loader, "read_local_players_data", lambda data_path: expected)

    with pytest.warns(UserWarning, match=r"aws sso login"):
        df = data_loader.load_players_data(profile="default", metadata_check_interval_seconds=0)

    assert df.equals(expected)


@pytest.mark.unit
def test_load_players_data_raises_without_fallback(monkeypatch):
    data_loader.clear_players_data_cache()
    monkeypatch.setattr(data_loader, "_load_from_s3_and_cache", lambda **kwargs: (_ for _ in ()).throw(data_loader.ProfileNotFound(profile="default")))

    with pytest.raises(data_loader.ProfileNotFound):
        data_loader.load_players_data(fallback_to_local=False, metadata_check_interval_seconds=0)
