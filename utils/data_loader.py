import os
from io import BytesIO
import logging
import warnings

import boto3
import pandas as pd
from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound

from utils.config import AWS_PROFILE, AWS_REGION, DATA_PATH, S3_BUCKET, S3_FALLBACK_TO_LOCAL, S3_KEY

logger = logging.getLogger(__name__)

_LAST_DATA_SOURCE = "unknown"
_LAST_DATA_LOCATION = "unknown"


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
    _set_data_source("local", data_path)
    return pd.read_csv(data_path)


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
    _set_data_source("s3", s3_uri)
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


def load_players_data(
    *,
    fallback_to_local: bool = S3_FALLBACK_TO_LOCAL,
    data_path: str = DATA_PATH,
    bucket: str = S3_BUCKET,
    key: str = S3_KEY,
    region: str = AWS_REGION,
    profile: str | None = AWS_PROFILE,
) -> pd.DataFrame:
    try:
        return read_s3_players_data(
            bucket=bucket,
            key=key,
            region=region,
            profile=profile,
        )
    except (BotoCoreError, ClientError, ProfileNotFound, OSError, ValueError) as exc:
        if not fallback_to_local:
            raise

        message = _format_s3_error_message(exc, data_path=data_path, profile=profile)
        logger.warning(message)
        warnings.warn(message, stacklevel=2)
        return read_local_players_data(data_path)
