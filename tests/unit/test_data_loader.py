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
def test_read_s3_players_data_reads_csv_from_s3(monkeypatch):
    csv_bytes = b"player_id,sessions_per_week,avg_session_time,spend,days_since_last_login,churn\n1,3,45,9.99,2,0\n"

    monkeypatch.setattr(
        data_loader.boto3,
        "Session",
        lambda region_name=None: FakeSession(content=csv_bytes),
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


@pytest.mark.unit
def test_load_players_data_falls_back_to_local(monkeypatch):
    expected = pd.DataFrame({"player_id": [1]})

    def fake_read_s3_players_data(**kwargs):
        raise data_loader.ProfileNotFound(profile="default")

    def fake_read_local_players_data(data_path):
        data_loader._set_data_source("local", data_path)
        return expected

    monkeypatch.setattr(data_loader, "read_s3_players_data", fake_read_s3_players_data)
    monkeypatch.setattr(data_loader, "read_local_players_data", fake_read_local_players_data)

    df = data_loader.load_players_data()

    assert df.equals(expected)
    assert data_loader.get_current_data_source()["source"] == "local"


@pytest.mark.unit
def test_load_players_data_raises_without_fallback(monkeypatch):
    def fake_read_s3_players_data(**kwargs):
        raise ClientError({"Error": {"Code": "403", "Message": "Forbidden"}}, "GetObject")

    monkeypatch.setattr(data_loader, "read_s3_players_data", fake_read_s3_players_data)

    with pytest.raises(ClientError):
        data_loader.load_players_data(fallback_to_local=False)
