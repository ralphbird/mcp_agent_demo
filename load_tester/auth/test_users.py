"""Test user pool generation and management for load testing."""

import random
from dataclasses import dataclass
from typing import Any

import uuid_utils.compat as uuid


@dataclass
class TestUser:
    """Test user with account and user identifiers."""

    account_id: str
    user_id: str

    def __post_init__(self) -> None:
        """Validate user identifiers after initialization."""
        if not self.account_id or not self.user_id:
            msg = "account_id and user_id must be non-empty"
            raise ValueError(msg)


class TestUserPool:
    """Manages pool of test users for load testing authentication."""

    def __init__(
        self,
        num_accounts: int = 1000,
        min_users_per_account: int = 100,
        max_users_per_account: int = 1000,
    ) -> None:
        """Initialize test user pool.

        Args:
            num_accounts: Number of test accounts to generate
            min_users_per_account: Minimum users per account
            max_users_per_account: Maximum users per account
        """
        self.num_accounts = num_accounts
        self.min_users_per_account = min_users_per_account
        self.max_users_per_account = max_users_per_account
        self._user_pool: list[TestUser] = []
        self._accounts_to_users: dict[str, list[TestUser]] = {}
        self._generated = False

    def _generate_pool(self) -> None:
        """Generate the complete test user pool."""
        if self._generated:
            return

        # Track all generated UUIDs to ensure uniqueness
        all_uuids: set[str] = set()

        for _ in range(self.num_accounts):
            # Generate unique account ID
            account_id = str(uuid.uuid7())
            while account_id in all_uuids:
                account_id = str(uuid.uuid7())
            all_uuids.add(account_id)

            # Determine number of users for this account
            users_for_account = random.randint(
                self.min_users_per_account, self.max_users_per_account
            )
            account_users: list[TestUser] = []

            for _ in range(users_for_account):
                # Generate unique user ID
                user_id = str(uuid.uuid7())
                while user_id in all_uuids:
                    user_id = str(uuid.uuid7())
                all_uuids.add(user_id)

                # Create test user
                test_user = TestUser(account_id=account_id, user_id=user_id)
                account_users.append(test_user)
                self._user_pool.append(test_user)

            # Store users by account for efficient lookup
            self._accounts_to_users[account_id] = account_users

        self._generated = True

    def get_random_user(self) -> TestUser:
        """Get a random test user from the pool.

        Returns:
            Random TestUser instance

        Raises:
            RuntimeError: If pool generation fails
        """
        if not self._generated:
            self._generate_pool()

        if not self._user_pool:
            msg = "No test users available in pool"
            raise RuntimeError(msg)

        return random.choice(self._user_pool)

    def get_random_users(self, count: int) -> list[TestUser]:
        """Get multiple random test users from the pool.

        Args:
            count: Number of users to return

        Returns:
            List of random TestUser instances (may contain duplicates)

        Raises:
            ValueError: If count is invalid
            RuntimeError: If pool generation fails
        """
        if count <= 0:
            msg = "Count must be positive"
            raise ValueError(msg)

        if not self._generated:
            self._generate_pool()

        if not self._user_pool:
            msg = "No test users available in pool"
            raise RuntimeError(msg)

        return [random.choice(self._user_pool) for _ in range(count)]

    def get_users_for_account(self, account_id: str) -> list[TestUser]:
        """Get all users for a specific account.

        Args:
            account_id: Account identifier

        Returns:
            List of TestUser instances for the account

        Raises:
            KeyError: If account_id not found
            RuntimeError: If pool generation fails
        """
        if not self._generated:
            self._generate_pool()

        if account_id not in self._accounts_to_users:
            msg = f"Account {account_id} not found in test pool"
            raise KeyError(msg)

        return self._accounts_to_users[account_id].copy()

    def get_account_ids(self) -> list[str]:
        """Get all account IDs in the pool.

        Returns:
            List of account identifiers

        Raises:
            RuntimeError: If pool generation fails
        """
        if not self._generated:
            self._generate_pool()

        return list(self._accounts_to_users.keys())

    def get_pool_stats(self) -> dict[str, Any]:
        """Get statistics about the test user pool.

        Returns:
            Dictionary with pool statistics

        Raises:
            RuntimeError: If pool generation fails
        """
        if not self._generated:
            self._generate_pool()

        total_users = len(self._user_pool)
        total_accounts = len(self._accounts_to_users)

        # Calculate users per account statistics
        users_per_account = [len(users) for users in self._accounts_to_users.values()]
        min_users = min(users_per_account) if users_per_account else 0
        max_users = max(users_per_account) if users_per_account else 0
        avg_users = sum(users_per_account) / len(users_per_account) if users_per_account else 0

        return {
            "total_accounts": total_accounts,
            "total_users": total_users,
            "min_users_per_account": min_users,
            "max_users_per_account": max_users,
            "avg_users_per_account": round(avg_users, 2),
            "configured_accounts": self.num_accounts,
            "configured_min_users": self.min_users_per_account,
            "configured_max_users": self.max_users_per_account,
        }


# Global test user pool instance with default configuration
_global_test_pool: TestUserPool | None = None


def get_test_user_pool() -> TestUserPool:
    """Get the global test user pool instance.

    Returns:
        Global TestUserPool instance with default configuration
    """
    global _global_test_pool
    if _global_test_pool is None:
        _global_test_pool = TestUserPool()
    return _global_test_pool


def get_random_test_user() -> TestUser:
    """Get a random test user from the global pool.

    Returns:
        Random TestUser instance
    """
    return get_test_user_pool().get_random_user()


def get_random_test_users(count: int) -> list[TestUser]:
    """Get multiple random test users from the global pool.

    Args:
        count: Number of users to return

    Returns:
        List of random TestUser instances (may contain duplicates)
    """
    return get_test_user_pool().get_random_users(count)
