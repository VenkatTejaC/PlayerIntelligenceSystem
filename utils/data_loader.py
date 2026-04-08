import os
from io import BytesIO
import logging
import time
import warnings

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound

from utils.config import (
    AWS_PROFILE,
    AWS_REGION,
    DATA_PATH,
    S3_BUCKET,
    S3_FALLBACK_TO_LOCAL,
    S3_KEY,
    S3_METADATA_CHECK_INTERVAL_SECONDS,
)

logger = logging.getLogger(__name__)

_LAST_DATA_SOURCE = "unknown"
_LAST_DATA_LOCATION = "unknown"
_DATA_CACHE = {
    "df": None,
    "source": "unknown",
    "location": "unknown",
    "s3_metadata": None,
    "last_checked_at": 0.0,
}


def _set_data_source(source: str, location: str) -> None:
    global _LAST_DATA_SOURCE, _LAST_DATA_LOCATION
    _LAST_DATA_SOURCE = source
    _LAST_DATA_LOCATION = location


def _set_cache(df: pd.DataFrame, *, source: str, location: str, s3_metadata: dict | None) -> pd.DataFrame:
    _DATA_CACHE["df"] = df
    _DATA_CACHE["source"] = source
    _DATA_CACHE["location"] = location
    _DATA_CACHE["s3_metadata"] = s3_metadata
    _DATA_CACHE["last_checked_at"] = time.time()
    _set_data_source(source, location)
    return df


def clear_players_data_cache() -> None:
    _DATA_CACHE["df"] = None
    _DATA_CACHE["source"] = "unknown"
    _DATA_CACHE["location"] = "unknown"
    _DATA_CACHE["s3_metadata"] = None
    _DATA_CACHE["last_checked_at"] = 0.0
    _set_data_source("unknown", "unknown")


def get_current_data_source() -> dict[str, str]:
    return {
        "source": _LAST_DATA_SOURCE,
        "location": _LAST_DATA_LOCATION,
    }


def get_s3_uri(bucket: str = S3_BUCKET, key: str = S3_KEY) -> str:
    return f"s3://{bucket}/{key}"


def get_aws_profile(profile: str | None = AWS_PROFILE) -> str | None:
    env_profile = os.getenv("AWS_PROFILE")
    if env_profile:
        return env_profile
    return profile


def create_s3_session(*, region: str = AWS_REGION, profile: str | None = AWS_PROFILE):
    resolved_profile = get_aws_profile(profile)
    if resolved_profile in (None, "", "default"):
        return boto3.Session(region_name=region)
    return boto3.Session(profile_name=resolved_profile, region_name=region)


def get_sso_login_hint(profile: str | None = AWS_PROFILE) -> str:
    resolved_profile = get_aws_profile(profile)
    if resolved_profile:
        return f"aws sso login --profile {resolved_profile}"
    return "aws sso login"


def read_local_players_data(data_path: str = DATA_PATH) -> pd.DataFrame:
    logger.info("Loading player data from local file: %s", data_path)
    return pd.read_csv(data_path)


def get_s3_object_metadata(
    *,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
    profile: str | None = AWS_PROFILE,
) -> dict[str, str]:
    session = create_s3_session(region=region, profile=profile)
    client = session.client("s3")
    response = client.head_object(Bucket=bucket, Key=key)
    return {
        "etag": str(response.get("ETag", "")).strip('"'),
        "last_modified": response["LastModified"].isoformat() if response.get("LastModified") else "",
    }


def read_s3_players_data(
    *,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
    profile: str | None = AWS_PROFILE,
) -> pd.DataFrame:
    s3_uri = get_s3_uri(bucket=bucket, key=key)
    resolved_profile = get_aws_profile(profile)
    logger.info(
        "Loading player data from S3: %s (region=%s, profile=%s)",
        s3_uri,
        region,
        resolved_profile or "default-chain",
    )
    session = create_s3_session(region=region, profile=profile)
    client = session.client("s3")
    response = client.get_object(Bucket=bucket, Key=key)
    body = response["Body"].read()
    logger.info("Loaded player data from S3 successfully: %s", s3_uri)
    return pd.read_csv(BytesIO(body))


def _format_s3_error_message(exc: Exception, *, data_path: str, profile: str | None) -> str:
    message = f"Falling back to local data at {data_path} because S3 read failed: {exc}"
    if isinstance(exc, ClientError):
        error_code = exc.response.get("Error", {}).get("Code")
        if error_code in {"ExpiredToken", "ExpiredTokenException"}:
            message = (
                f"{message}. Your AWS SSO session appears to be expired. "
                f"Refresh it with: {get_sso_login_hint(profile)}"
            )
    return message


def _load_from_s3_and_cache(*, bucket: str, key: str, region: str, profile: str | None) -> pd.DataFrame:
    metadata = get_s3_object_metadata(bucket=bucket, key=key, region=region, profile=profile)
    df = read_s3_players_data(bucket=bucket, key=key, region=region, profile=profile)
    return _set_cache(df, source="s3", location=get_s3_uri(bucket=bucket, key=key), s3_metadata=metadata)


def _load_from_local_and_cache(*, data_path: str) -> pd.DataFrame:
    df = read_local_players_data(data_path)
    return _set_cache(df, source="local", location=data_path, s3_metadata=None)


def _handle_s3_failure(*, exc: Exception, fallback_to_local: bool, data_path: str, profile: str | None) -> pd.DataFrame:
    if not fallback_to_local:
        raise exc

    message = _format_s3_error_message(exc, data_path=data_path, profile=profile)
    logger.warning(message)
    warnings.warn(message, stacklevel=2)
    return _load_from_local_and_cache(data_path=data_path)


def load_players_data(
    *,
    fallback_to_local: bool = S3_FALLBACK_TO_LOCAL,
    data_path: str = DATA_PATH,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
    profile: str | None = AWS_PROFILE,
    metadata_check_interval_seconds: int = S3_METADATA_CHECK_INTERVAL_SECONDS,
) -> pd.DataFrame:
    cached_df = _DATA_CACHE["df"]
    if cached_df is None:
        try:
            return _load_from_s3_and_cache(bucket=bucket, key=key, region=region, profile=profile)
        except (BotoCoreError, ClientError, ProfileNotFound, OSError, ValueError) as exc:
            return _handle_s3_failure(
                exc=exc,
                fallback_to_local=fallback_to_local,
                data_path=data_path,
                profile=profile,
            )

    elapsed = time.time() - float(_DATA_CACHE["last_checked_at"])
    if elapsed < metadata_check_interval_seconds:
        _set_data_source(_DATA_CACHE["source"], _DATA_CACHE["location"])
        return cached_df

    if _DATA_CACHE["source"] == "s3":
        try:
            metadata = get_s3_object_metadata(bucket=bucket, key=key, region=region, profile=profile)
            if metadata != _DATA_CACHE["s3_metadata"]:
                logger.info("Detected S3 object change for %s. Reloading data.", get_s3_uri(bucket=bucket, key=key))
                return _load_from_s3_and_cache(bucket=bucket, key=key, region=region, profile=profile)

            _DATA_CACHE["last_checked_at"] = time.time()
            _set_data_source(_DATA_CACHE["source"], _DATA_CACHE["location"])
            return cached_df
        except (BotoCoreError, ClientError, ProfileNotFound, OSError, ValueError) as exc:
            return _handle_s3_failure(
                exc=exc,
                fallback_to_local=fallback_to_local,
                data_path=data_path,
                profile=profile,
            )

    try:
        logger.info("Rechecking S3 after local fallback to see if remote data is available again.")
        return _load_from_s3_and_cache(bucket=bucket, key=key, region=region, profile=profile)
    except (BotoCoreError, ClientError, ProfileNotFound, OSError, ValueError) as exc:
        return _handle_s3_failure(
            exc=exc,
            fallback_to_local=fallback_to_local,
            data_path=data_path,
            profile=profile,
        )
