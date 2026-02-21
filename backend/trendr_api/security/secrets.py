from __future__ import annotations

import base64
import hashlib
import hmac
import os

from ..config import settings


class SecretEncryptionError(RuntimeError):
    """Raised when a secret cannot be encrypted/decrypted."""


def _encryption_material() -> str:
    # Prefer a dedicated key, but keep local-dev fallback to avoid blocking setup.
    return (settings.secrets_encryption_key or settings.jwt_secret or "").strip()


def _key_bytes() -> bytes:
    material = _encryption_material()
    if not material:
        raise SecretEncryptionError("SECRETS_ENCRYPTION_KEY is not configured")
    return hashlib.sha256(material.encode("utf-8")).digest()


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = bytearray()
    counter = 0
    while len(output) < length:
        block = hmac.new(
            key,
            nonce + counter.to_bytes(8, "big"),
            hashlib.sha256,
        ).digest()
        output.extend(block)
        counter += 1
    return bytes(output[:length])


def encrypt_secret(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise SecretEncryptionError("Secret value cannot be empty")
    key = _key_bytes()
    plaintext = normalized.encode("utf-8")
    nonce = os.urandom(16)
    stream = _keystream(key, nonce, len(plaintext))
    ciphertext = bytes(b ^ s for b, s in zip(plaintext, stream))
    tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
    token = base64.urlsafe_b64encode(nonce + tag + ciphertext)
    return token.decode("utf-8")


def decrypt_secret(token: str) -> str:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8"))
        if len(raw) < 48:
            raise ValueError("ciphertext too short")
        nonce = raw[:16]
        tag = raw[16:48]
        ciphertext = raw[48:]
        key = _key_bytes()
        expected_tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("invalid ciphertext authentication tag")
        stream = _keystream(key, nonce, len(ciphertext))
        plaintext = bytes(b ^ s for b, s in zip(ciphertext, stream))
        return plaintext.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise SecretEncryptionError("Unable to decrypt stored secret") from exc


def secret_hint(value: str) -> str:
    normalized = value.strip()
    if len(normalized) < 4:
        return "****"
    return f"***{normalized[-4:]}"
