#!/usr/bin/env python3
"""JWT token generation utility script for testing and development.

This script allows you to generate JWT tokens for testing the currency API
with authentication. It can generate tokens for specific users or create
test tokens from the load testing user pool.
"""

import argparse
import sys

from currency_app.auth.jwt_auth import generate_jwt_token
from load_tester.auth.test_users import get_random_test_users, get_test_user_pool


def generate_single_token(account_id: str, user_id: str, expires_in: int | None = None) -> None:
    """Generate a single JWT token for specified account and user.

    Args:
        account_id: Account identifier
        user_id: User identifier
        expires_in: Token expiration in seconds (None for no expiration)
    """
    try:
        token = generate_jwt_token(
            account_id=account_id, user_id=user_id, expires_in_seconds=expires_in
        )

        print(f"Generated JWT token for account_id={account_id}, user_id={user_id}")
        print(f"Token: {token}")
        print(f"Authorization Header: Bearer {token}")

        if expires_in is None:
            print("Expiration: Never (development mode)")
        else:
            print(f"Expires in: {expires_in} seconds")

    except Exception as e:
        print(f"Error generating token: {e}", file=sys.stderr)
        sys.exit(1)


def generate_test_pool_tokens(count: int = 10) -> None:
    """Generate tokens from the test user pool.

    Args:
        count: Number of tokens to generate
    """
    try:
        # Get random test users from pool
        test_users = get_random_test_users(count)

        print(f"Generated {len(test_users)} JWT tokens from test user pool:")
        print()

        for i, user in enumerate(test_users, 1):
            token = generate_jwt_token(
                account_id=user.account_id,
                user_id=user.user_id,
                expires_in_seconds=None,  # No expiration for testing
            )

            print(f"Token #{i}:")
            print(f"  Account ID: {user.account_id}")
            print(f"  User ID: {user.user_id}")
            print(f"  Token: {token}")
            print(f"  Auth Header: Bearer {token}")
            print()

    except Exception as e:
        print(f"Error generating test pool tokens: {e}", file=sys.stderr)
        sys.exit(1)


def show_test_pool_stats() -> None:
    """Show statistics about the test user pool."""
    try:
        pool = get_test_user_pool()
        stats = pool.get_pool_stats()

        print("Test User Pool Statistics:")
        print(f"  Total Accounts: {stats['total_accounts']}")
        print(f"  Total Users: {stats['total_users']}")
        print(
            f"  Users per Account: {stats['min_users_per_account']}-{stats['max_users_per_account']} (avg: {stats['avg_users_per_account']})"
        )
        print()

    except Exception as e:
        print(f"Error getting pool stats: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI interface for JWT token generation."""
    parser = argparse.ArgumentParser(
        description="Generate JWT tokens for currency API testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate token for specific user
  python scripts/generate_jwt_tokens.py --account-id "acc-123" --user-id "user-456"

  # Generate token with 1 hour expiration
  python scripts/generate_jwt_tokens.py --account-id "acc-123" --user-id "user-456" --expires-in 3600

  # Generate 5 tokens from test pool
  python scripts/generate_jwt_tokens.py --test-pool --count 5

  # Show test pool statistics
  python scripts/generate_jwt_tokens.py --stats
        """,
    )

    # Token generation options
    parser.add_argument("--account-id", help="Account ID for token generation")
    parser.add_argument("--user-id", help="User ID for token generation")
    parser.add_argument(
        "--expires-in", type=int, help="Token expiration in seconds (default: no expiration)"
    )

    # Test pool options
    parser.add_argument(
        "--test-pool", action="store_true", help="Generate tokens from test user pool"
    )
    parser.add_argument(
        "--count", type=int, default=10, help="Number of test pool tokens to generate (default: 10)"
    )

    # Utility options
    parser.add_argument("--stats", action="store_true", help="Show test user pool statistics")

    args = parser.parse_args()

    # Validate arguments
    if args.stats:
        show_test_pool_stats()
        return

    if args.test_pool:
        generate_test_pool_tokens(args.count)
        return

    if args.account_id and args.user_id:
        generate_single_token(args.account_id, args.user_id, args.expires_in)
        return

    # Invalid argument combinations
    if args.account_id and not args.user_id:
        print("Error: --user-id is required when --account-id is specified", file=sys.stderr)
        sys.exit(1)

    if args.user_id and not args.account_id:
        print("Error: --account-id is required when --user-id is specified", file=sys.stderr)
        sys.exit(1)

    # No valid options provided
    parser.print_help()
    print(
        "\nError: Must specify either --stats, --test-pool, or both --account-id and --user-id",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
