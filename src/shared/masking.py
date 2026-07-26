"""Fail-closed analyst PII masking and secret-safe structured redaction."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

PII_KEYS = frozenset({"name", "full_name", "phone", "phone_number", "email", "address", "account_number", "bank_account", "upi_id", "aadhaar", "aadhaar_hash", "dob", "date_of_birth", "imei"})


def mask_value(value: Any, *, keep_last: int = 0) -> str:
    text = str(value)
    if keep_last and len(text) > keep_last:
        return "*" * (len(text) - keep_last) + text[-keep_last:]
    return "[MASKED]"


def mask_record(value: Any, *, role: str) -> Any:
    """Recursively mask PII for Analyst; preserve structure and non-PII values."""

    if role != "Analyst":
        return value
    if isinstance(value, Mapping):
        return {key: mask_value(item, keep_last=4 if key in {"phone", "phone_number", "account_number", "bank_account"} else 0) if str(key).casefold() in PII_KEYS else mask_record(item, role=role) for key, item in value.items()}
    if isinstance(value, list):
        return [mask_record(item, role=role) for item in value]
    if isinstance(value, tuple):
        return tuple(mask_record(item, role=role) for item in value)
    return value


def redact_secrets(value: Any) -> Any:
    """Redact common credential-bearing keys from logs/errors/exports."""

    secret_keys = {"authorization", "token", "access_token", "refresh_token", "password", "secret", "api_key", "credential"}
    if isinstance(value, Mapping):
        return {key: "[REDACTED]" if str(key).casefold() in secret_keys else redact_secrets(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_secrets(item) for item in value)
    return value


__all__ = ["PII_KEYS", "mask_record", "mask_value", "redact_secrets"]
