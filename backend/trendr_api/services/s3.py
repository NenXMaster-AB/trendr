from __future__ import annotations

import logging
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from ..config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
        )
    return _client


def ensure_bucket() -> None:
    client = _get_client()
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
        logger.info("s3_bucket_exists", extra={"bucket": settings.s3_bucket})
    except ClientError:
        client.create_bucket(Bucket=settings.s3_bucket)
        client.put_bucket_policy(
            Bucket=settings.s3_bucket,
            Policy=(
                '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
                '"Principal":"*","Action":"s3:GetObject",'
                f'"Resource":"arn:aws:s3:::{settings.s3_bucket}/*"'
                "}]}"
            ),
        )
        logger.info("s3_bucket_created", extra={"bucket": settings.s3_bucket})


def upload_bytes(
    data: bytes,
    key: str,
    content_type: str = "application/octet-stream",
) -> str:
    client = _get_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return f"{settings.s3_public_url}/{key}"
