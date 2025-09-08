"""JWT token generation and caching for load testing."""

from typing import Any

from load_tester.auth.jwt_utils import generate_jwt_token
from load_tester.auth.test_users import TestUser


class JWTTokenManager:
    """Manages JWT token generation and caching for load testing."""

    def __init__(self) -> None:
        """Initialize JWT token manager."""
        self._token_cache: dict[tuple[str, str], str] = {}

    def get_token_for_user(self, test_user: TestUser) -> str:
        """Get or generate JWT token for a test user.

        Args:
            test_user: Test user to generate token for

        Returns:
            JWT token string

        Raises:
            ValueError: If test_user is invalid
        """
        if not test_user or not test_user.account_id or not test_user.user_id:
            msg = "Valid test user with account_id and user_id required"
            raise ValueError(msg)

        # Create cache key from account_id and user_id
        cache_key = (test_user.account_id, test_user.user_id)

        # Return cached token if available
        if cache_key in self._token_cache:
            return self._token_cache[cache_key]

        # Generate new token (no expiration for development/testing)
        token = generate_jwt_token(
            account_id=test_user.account_id,
            user_id=test_user.user_id,
            expires_in_seconds=None,  # No expiration
        )

        # Cache the token
        self._token_cache[cache_key] = token

        return token

    def get_tokens_for_users(self, test_users: list[TestUser]) -> list[str]:
        """Get or generate JWT tokens for multiple test users.

        Args:
            test_users: List of test users

        Returns:
            List of JWT token strings in same order as input

        Raises:
            ValueError: If any test_user is invalid
        """
        return [self.get_token_for_user(user) for user in test_users]

    def get_authorization_header(self, test_user: TestUser) -> str:
        """Get Authorization header value for a test user.

        Args:
            test_user: Test user to generate header for

        Returns:
            Authorization header value (Bearer <token>)

        Raises:
            ValueError: If test_user is invalid
        """
        token = self.get_token_for_user(test_user)
        return f"Bearer {token}"

    def clear_cache(self) -> None:
        """Clear the token cache."""
        self._token_cache.clear()

    def get_cache_stats(self) -> dict[str, Any]:
        """Get statistics about the token cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_tokens": len(self._token_cache),
            "cache_keys": list(self._token_cache.keys())
            if len(self._token_cache) <= 10
            else "too_many_to_display",
        }

    def preload_tokens_for_users(self, test_users: list[TestUser]) -> int:
        """Preload tokens for a list of test users.

        Args:
            test_users: List of test users to preload tokens for

        Returns:
            Number of new tokens generated (not already cached)

        Raises:
            ValueError: If any test_user is invalid
        """
        new_tokens_generated = 0

        for test_user in test_users:
            if not test_user or not test_user.account_id or not test_user.user_id:
                msg = "Valid test user with account_id and user_id required"
                raise ValueError(msg)

            cache_key = (test_user.account_id, test_user.user_id)

            # Only generate if not already cached
            if cache_key not in self._token_cache:
                token = generate_jwt_token(
                    account_id=test_user.account_id,
                    user_id=test_user.user_id,
                    expires_in_seconds=None,  # No expiration
                )
                self._token_cache[cache_key] = token
                new_tokens_generated += 1

        return new_tokens_generated


# Global JWT token manager instance
_global_token_manager: JWTTokenManager | None = None


def get_jwt_token_manager() -> JWTTokenManager:
    """Get the global JWT token manager instance.

    Returns:
        Global JWTTokenManager instance
    """
    global _global_token_manager
    if _global_token_manager is None:
        _global_token_manager = JWTTokenManager()
    return _global_token_manager


def get_token_for_user(test_user: TestUser) -> str:
    """Get or generate JWT token for a test user using global manager.

    Args:
        test_user: Test user to generate token for

    Returns:
        JWT token string
    """
    return get_jwt_token_manager().get_token_for_user(test_user)


def get_authorization_header_for_user(test_user: TestUser) -> str:
    """Get Authorization header for a test user using global manager.

    Args:
        test_user: Test user to generate header for

    Returns:
        Authorization header value (Bearer <token>)
    """
    return get_jwt_token_manager().get_authorization_header(test_user)
