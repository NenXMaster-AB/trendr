from __future__ import annotations

from unittest.mock import MagicMock, patch

from trendr_api.services import s3 as s3_module


def test_ensure_bucket_creates_when_missing():
    mock_client = MagicMock()
    from botocore.exceptions import ClientError

    mock_client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadBucket",
    )

    with patch.object(s3_module, "_get_client", return_value=mock_client):
        s3_module.ensure_bucket()

    mock_client.create_bucket.assert_called_once()
    mock_client.put_bucket_policy.assert_called_once()


def test_ensure_bucket_skips_when_exists():
    mock_client = MagicMock()
    mock_client.head_bucket.return_value = {}

    with patch.object(s3_module, "_get_client", return_value=mock_client):
        s3_module.ensure_bucket()

    mock_client.create_bucket.assert_not_called()


def test_upload_bytes_returns_url():
    mock_client = MagicMock()

    with patch.object(s3_module, "_get_client", return_value=mock_client):
        url = s3_module.upload_bytes(b"hello", "test/image.png", "image/png")

    mock_client.put_object.assert_called_once()
    assert "test/image.png" in url
