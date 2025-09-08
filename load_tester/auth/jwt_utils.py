"""Standalone JWT token generation utilities for load testing."""

import time
from typing import Any

import jwt

from load_tester.config import LoadTesterSettings


def generate_jwt_token(
    account_id: str,
    user_id: str,
    expires_in_seconds: int | None = None,
    settings: LoadTesterSettings | None = None,
) -> str:
    """Generate JWT token for load testing.

    Args:
        account_id: Account identifier
        user_id: User identifier
        expires_in_seconds: Token expiration time (None for no expiration)
        settings: Load tester settings (will create new if None)

    Returns:
        JWT token string

    Raises:
        ValueError: If account_id or user_id are invalid
    """
    if not account_id or not account_id.strip():
        msg = "account_id must be a non-empty string"
        raise ValueError(msg)
    if not user_id or not user_id.strip():
        msg = "user_id must be a non-empty string"
        raise ValueError(msg)

    if settings is None:
        settings = LoadTesterSettings()

    # Prepare token payload
    payload: dict[str, Any] = {
        "account_id": account_id.strip(),
        "user_id": user_id.strip(),
        "iat": int(time.time()),  # Issued at
    }

    # Add expiration if specified
    if expires_in_seconds is not None:
        payload["exp"] = int(time.time()) + expires_in_seconds

    # Generate token
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
