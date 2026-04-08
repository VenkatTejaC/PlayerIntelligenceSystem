from io import BytesIO
import warnings

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound

from utils.config import AWS_REGION, DATA_PATH, S3_BUCKET, S3_FALLBACK_TO_LOCAL, S3_KEY

_LAST_DATA_SOURCE = "local"
_LAST_DATA_LOCATION = DATA_PATH


def clear_players_data_cache() -> None:
    return None


def _set_data_source(source: str, location: str) -> None:
    global _LAST_DATA_SOURCE, _LAST_DATA_LOCATION
    _LAST_DATA_SOURCE = source
    _LAST_DATA_LOCATION = location


def get_current_data_source() -> dict[str, str]:
    return {
        "source": _LAST_DATA_SOURCE,
        "location": _LAST_DATA_LOCATION,
    }


def get_s3_uri(bucket: str = S3_BUCKET, key: str = S3_KEY) -> str:
    return f"s3://{bucket}/{key}"


def read_local_players_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    _set_data_source("local", data_path)
    return pd.read_csv(data_path)


def read_s3_players_data(
    *,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
) -> pd.DataFrame:
    session = boto3.Session(region_name=region)
    client = session.client("s3")
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    s3_uri = get_s3_uri(bucket=bucket, key=key)
    _set_data_source("s3", s3_uri)
    return pd.read_csv(BytesIO(body))


def load_players_data(
    data_path: str = DATA_PATH,
    *,
    fallback_to_local: bool = S3_FALLBACK_TO_LOCAL,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
) -> pd.DataFrame:
    try:
        return read_s3_players_data(bucket=bucket, key=key, region=region)
    except (BotoCoreError, ClientError, NoCredentialsError, ProfileNotFound, OSError, ValueError) as exc:
        if not fallback_to_local:
            raise
        warnings.warn(
            f"Falling back to local data at {data_path} because S3 read failed: {exc}",
            stacklevel=2,
        )
        return read_local_players_data(data_path)
